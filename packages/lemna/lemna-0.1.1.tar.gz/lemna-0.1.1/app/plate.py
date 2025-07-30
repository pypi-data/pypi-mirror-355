class Plate:
    def __init__(self, label, rows, cols, wells, row_start_letter='A'):
        self.label = label
        self.rows = rows
        self.cols = cols
        self.wells = wells
        self.row_start_letter = row_start_letter

    def well_count(self):
        return self.rows * self.cols
    
    def get_well_label(self, index):
        if self.cols == 0:
            return ''
        well_row = index // self.cols
        well_col = index % self.cols   
        label = f"{chr(ord(self.row_start_letter) + well_col)}{well_row + 1}"
        return label