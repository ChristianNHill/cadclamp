// Unthreaded spacer: 16 OD x 5 long, 10 mm through-bore.
outer_diameter = 16;
bore_diameter = 10;
length = 5;
chamfer = 0.4;  // bottom chamfer keeps elephant's foot off the bore and rim
$fn = 96;

difference() {
    rotate_extrude()
        polygon([
            [bore_diameter/2 + chamfer, 0], [outer_diameter/2 - chamfer, 0],
            [outer_diameter/2, chamfer], [outer_diameter/2, length],
            [bore_diameter/2, length], [bore_diameter/2, chamfer]
        ]);
}
