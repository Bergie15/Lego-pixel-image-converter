from virtual_robot import VirtualRobot

COLOR_BINS = {
    'R':(-2,0),
    'U':(-3,0),
    'Y':(-4,0),
    'G':(-5,0),
    'W':(-6,0),
    'B':(-7,0)
}

def build(pixel_map):
    robot = VirtualRobot()

    for y, row in enumerate(pixel_map):
        for x, color in enumerate(row):
            # color may be a short bin code (e.g. 'R') or a full color name
            bin_key = color
            if bin_key not in COLOR_BINS:
                lname = bin_key.lower()
                # map common color name keywords to bin codes
                if 'red' in lname or 'reddish' in lname:
                    bin_key = 'R'
                elif 'blue' in lname:
                    bin_key = 'U'
                elif 'yellow' in lname:
                    bin_key = 'Y'
                elif 'green' in lname or 'lime' in lname or 'olive' in lname:
                    bin_key = 'G'
                elif 'white' in lname:
                    bin_key = 'W'
                else:
                    # everything else (gray, black, brown, tan, orange, purple, etc.)
                    # will use the 'B' bin (fallback)
                    bin_key = 'B'

            robot.move_to(*COLOR_BINS[bin_key])
            robot.pick(bin_key)
            robot.move_to(x, y)
            robot.place()
