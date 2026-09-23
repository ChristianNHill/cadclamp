// t3-006 finned base plate
base_length = 80;
base_width = 40;
base_thickness = 5;
fin_count = 6;
fin_thickness = 2.4;
fin_height = 25;
fin_pitch = (base_length - fin_thickness) / (fin_count - 1);

union() {
    translate([-base_length / 2, -base_width / 2, 0])
        cube([base_length, base_width, base_thickness]);
    for (i = [0 : fin_count - 1])
        translate([-base_length / 2 + i * fin_pitch, -base_width / 2, base_thickness - 0.01])
            cube([fin_thickness, base_width, fin_height + 0.01]);
}
