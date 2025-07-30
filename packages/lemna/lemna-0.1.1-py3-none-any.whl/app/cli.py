from app.image_processor import ImageProcessor
from app.well_detector import WellDetector
from app.well_analyzer import WellAnalyzer
from app.visualizer import Visualizer
from app.hsv_thresholder import HsvThresolder
from app.config_manager import ConfigManager
from app.plate import Plate
from pathlib import Path
import os
import click




@click.group()
def cli():
    pass

@cli.command()
@click.option(
    "-i",
    "--image",
    "image",
    type=click.Path(path_type=Path, dir_okay=False),
    multiple=False,
    help="The image file to open.",
)
@click.option(
    "-w",
    "--width",
    "width",
    type=click.INT,
    help="The desired width to display the image.",
)
@click.option(
    "-c",
    "--config",
    "config",
    type=click.Path(path_type=Path),
    help="The config to be updated with the chosen HSV range.",
)
def threshold(image, width, config):
    """Helper to determine optimal threshold values for masking items of interest"""
    thresholder = HsvThresolder(image)
    lower_bound, upper_bound = thresholder.threshold(width)
    new_min_max_threshold = {
        "well_analyzer": {
            "hsv_lower_bound": lower_bound,
            "hsv_upper_bound": upper_bound
        }
    }
    config_manager = ConfigManager(config)
    config_manager.update(new_min_max_threshold)
    config_manager.write()
    click.echo(f"Updated thresholds in {config}")

@cli.command()
@click.option(
    "-i",
    "--image",
    "images",
    type=click.Path(path_type=Path),
    multiple=False,
    help="The image file to open.",
)
@click.option('--dp', default=1, help='Inverse ratio of the accumulator resolution to the image resolution.')
@click.option('--min_dist', default=270, help='Minimum distance between the centers of detected circles.')
@click.option('--param1', default=45, help='First method-specific parameter for the edge detection.')
@click.option('--param2', default=20, help='Second method-specific parameter for the center detection.')
@click.option('--min_radius', default=120, help='Minimum circle radius to detect.')
@click.option('--max_radius', default=145, help='Maximum circle radius to detect.')
@click.option(
    "-c",
    "--config",
    "config",
    type=click.Path(path_type=Path),
    help="The config to use. Cannot be combined with individual params for configuration.",
)
@click.option(
    "-o",
    "--output",
    "output",
    type=click.Path(path_type=Path, dir_okay=True),
    multiple=False,
    help="The name of the directory to output to.",
)
def process(images, config, output, dp, min_dist, param1, param2, min_radius, max_radius):
    """Processes images"""
    
    hsv_lower_bound = (20, 18, 0)
    hsv_upper_bound =  (179, 255, 91)
    rows = 6
    cols = 4
    well_count = 24
    eps = 350
    is_plate_grouping_enabled = True

    if config:
        try:
            config_manager = ConfigManager(config)
            config_manager.load()
            
            well_detector_config = config_manager.get('well_detector')
            dp = well_detector_config.get('dp')
            min_dist = well_detector_config.get('min_dist')
            param1 = well_detector_config.get('param1')
            param2 = well_detector_config.get('param2')
            min_radius = well_detector_config.get('min_radius')
            max_radius = well_detector_config.get('max_radius')
            eps = well_detector_config.get('eps') or eps

            well_analyzer_config = config_manager.get('well_analyzer')
            hsv_lower_bound = tuple(well_analyzer_config.get('hsv_lower_bound'))
            hsv_upper_bound = tuple(well_analyzer_config.get('hsv_upper_bound'))

            plate_config = config_manager.get('plate')
            rows = plate_config.get('rows')
            cols = plate_config.get('cols')
            well_count = plate_config.get('well_count')
            is_plate_grouping_enabled = plate_config.get('grouping')
        except Exception as e:
            click.echo(e)
            click.echo(f"Failed while processing config file {config}")
    else:
        # If no config file, use CLI values with defaults
        dp = dp or 1
        min_dist = min_dist or 270
        param1 = param1 or 45
        param2 = param2 or 20
        min_radius = min_radius or 120
        max_radius = max_radius or 145

    def process_image(image_path, output):
        click.echo(f'Processing {image_path}')
        # Step 1: Load and preprocess the image
        processor = ImageProcessor(image_path)
        blurred_image = processor.get_blurred_image()

        # Step 2: Detect and sort circles (wells)
        detector = WellDetector(blurred_image)
        wells = detector.detect_wells(dp, min_dist, param1, param2, min_radius, max_radius)
       
        sorted_wells = detector.sort_circles(wells)
        if is_plate_grouping_enabled:
            plates = detector.group_wells_into_plates(sorted_wells, plate_rows=rows, plate_cols=cols, eps=eps)
        else:
            plates = [Plate(
                label="Plate 1",
                rows=0, 
                cols=0, 
                wells=sorted_wells)]

        # Step 3: Analyze duckweed for each well
        analyzer = WellAnalyzer(processor.get_original_image(), hsv_lower_bound, hsv_upper_bound)
        visualizer = Visualizer(processor.get_original_image())

        csv_out = []
        csv_out.append("Plate,Well,Area")
        if is_plate_grouping_enabled:
            for plate in plates:
                for i, (x, y, r) in enumerate(plate.wells):
                    # Analyze the duckweed in the current well
                    contours, total_area = analyzer.analyze_plant_area(x, y, r)
            
                    # Draw the circle and contours on the image
                    visualizer.draw_contours(contours)


                    label = plate.get_well_label(i)
                    visualizer.add_text(x, y, r, f"{label}: {total_area} px")

                    # add well label and area to output
                    csv_out.append(f"{plate.label},{label},{total_area}")

                visualizer.draw_circles(plate.wells)
                visualizer.draw_plate_bounding_box(plate.wells, label=plate.label)
        else:
            for i, (x, y, r) in enumerate(sorted_wells):
                    # Analyze the duckweed in the current well
                    contours, total_area = analyzer.analyze_plant_area(x, y, r)
            
                    # Draw the circle and contours on the image
                    visualizer.draw_contours(contours)

                    visualizer.add_text(x, y, r, f"well {i}: {total_area} px")

                    # add well label and area to output
                    csv_out.append(f"1,well_{i},{total_area}")

            visualizer.draw_circles(sorted_wells)

            
        os.makedirs(output, exist_ok=True)
        out_name = os.path.splitext(os.path.basename(image_path))[0]
        out_file = str(output) + "/" + out_name + ".csv"
        with open(out_file, 'w') as f:
            for line in csv_out:
                f.write(line + '\n')

        out_image = str(output) + "/" + out_name + "_annotated.png"
        visualizer.save_image(out_image)


    if images.is_dir():
        for image_path in images.iterdir():
            process_image(image_path, output)
    else:
        process_image(images, output)


@cli.command()
@click.option(
    "-f",
    "--file",
    "file",
    type=click.Path(path_type=Path),
    help="The config file path.",
)
def config(file):
    """Generates a new config file"""
    if file:
        config_manager = ConfigManager(file)
        config_manager.generate()
    else:
        config_manager = ConfigManager()
        config_manager.generate()

# # Run the program
if __name__ == "__main__":
    cli()
