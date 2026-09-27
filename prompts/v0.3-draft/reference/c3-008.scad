// GT2 20-tooth pulley printed hub down (v0.3 draft). The teeth and grooves
// run the full channel to Z 14.8; the flange's underside flares from the
// tooth tips out to 15 mm over 0.6 mm, a short chamfered overhang ring.
tooth_count = 20;
bore_diameter = 5;
belt_width = 6;
pitch_diameter = 12.22;
tooth_od = 11.71;
groove_r = 0.555;       // GT2 groove radius
groove_c = pitch_diameter/2 - 0.254 - 0.75 + groove_r;  // groove bottom 0.75 below the tips
hub_d = 15;
hub_h = 7.8;
teeth_top = 14.8;
flange_d = 15;
total = 16;
setscrew = 2.6;
rim = 0.6;
cone = (flange_d - tooth_od)/2 + 0.17;
$fn = 96;

module teeth2d() {
    difference() {
        circle(d = tooth_od, $fn = 10 * tooth_count);
        for (i = [0 : tooth_count - 1])
            rotate(i * 360 / tooth_count)
                translate([groove_c, 0]) circle(r = groove_r, $fn = 24);
    }
}

module drop_x(d, len) {
    // axis along X, point towards +Z
    rotate([0, 90, 0]) linear_extrude(len)
        hull() {
            circle(d = d, $fn = 32);
            translate([-d/2*sqrt(2), 0]) square(0.01, center = true);
        }
}

difference() {
    union() {
        cylinder(d = hub_d, h = hub_h);
        translate([0, 0, hub_h]) linear_extrude(teeth_top - hub_h) teeth2d();
        translate([0, 0, teeth_top - 0.1]) cylinder(d1 = tooth_od - 0.2, d2 = flange_d, h = total - rim - teeth_top + 0.1);
        translate([0, 0, total - rim]) cylinder(d = flange_d, h = rim);
    }
    translate([0, 0, -1]) cylinder(d = bore_diameter + 0.1, h = total + 2);
    translate([0, 0, hub_h/2]) {
        drop_x(setscrew, hub_d);
        rotate([0, 0, 90]) drop_x(setscrew, hub_d);
    }
}
