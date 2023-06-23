from utils import is_valid_hex_code
import logging

class InterfaceColor:

    def __init__(self, file = '/opt/iotrimmer/static/css/style.css') -> None:
        self.cssFileName = file
        self.load_color()
        self.colors = ['e30073', '000099', 'd66f1a', '009999', '6600ff', '990000', '009933'] # hex


    def __iter__(self) -> None:
        return ('#' + color for color in self.colors)


    def __len__(self) -> None:
        return len(self.colors)


    def load_color(self) -> None:
        with open(self.cssFileName, "r") as file:
            self.lines = file.readlines()
        self.color = self.lines[1][17:-2]


    def set_color(self, newColor :str) -> None:
        if self.color == newColor or not newColor:
            return
        if not is_valid_hex_code(newColor):
            logging.warning(f"Invalid interface color setting attempted with color: {newColor}")
            return
        self.lines[1] = f"  --accent-color:{newColor};\n"
        with open(self.cssFileName, "w") as file:
            file.writelines(self.lines)
        self.load_color()
        logging.info(f"Interface color set with color: {newColor}")
