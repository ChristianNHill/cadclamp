// Lift-off hinge printed assembled, knuckle axis vertical. The lower knuckle
// ends in a 45 degree cone and the upper knuckle's underside is the same cone
// raised by the clearance, so nothing prints over air.
hinge_length = 50.8;
leaf_width = 25.4;      // axis to leaf edge
clearance = 0.6;        // vertical offset of the cone interface (0.42 normal to it)
pin_d = 4.76;
pin_gap = 0.45;         // radial gap round the pin
side_gap = 0.45;        // leaf plate to the other knuckle
knuckle_r = 5;
thickness = 3;
hole_d = 4.4;
hole_x = 19.05;
hole_z = [9.525, 41.275];
$fn = 72;

split = hinge_length/2;
t = thickness;

module teardrop_y(d, len) {
    rotate([90, 0, 0]) linear_extrude(len, center = true)
        hull() {
            circle(d = d, $fn = 32);
            translate([0, d/2*sqrt(2)]) square(0.01, center = true);
        }
}

// solid below the interface cone (apex up), raised by dz
module below_cone(dz) {
    translate([0, 0, -1]) cylinder(r = knuckle_r + 2, h = split + dz + 1 - 2);
    translate([0, 0, split + dz - 2]) cylinder(r1 = knuckle_r + 2, r2 = 0, h = knuckle_r + 2);
}

module plate(x0, x1, z0, z1) {
    translate([x0, -t/2, z0]) cube([x1 - x0, t, z1 - z0]);
}

module holes(s) {
    for (z = hole_z) translate([s*hole_x, 0, z]) teardrop_y(hole_d, t + 2);
}

// pin leaf: lower knuckle, pin, plate along -X
difference() {
    union() {
        intersection() {
            cylinder(r = knuckle_r, h = hinge_length);
            below_cone(0);
        }
        cylinder(d = pin_d, h = hinge_length - 0.5);
        plate(-leaf_width, -knuckle_r - side_gap, 0, hinge_length);
        plate(-knuckle_r - side_gap - 0.1, -knuckle_r + 1, 0, split - 1);
    }
    holes(-1);
}

// lifting leaf: upper knuckle, plate along +X
difference() {
    union() {
        difference() {
            cylinder(r = knuckle_r, h = hinge_length);
            below_cone(clearance);
            translate([0, 0, -1]) cylinder(d = pin_d + 2*pin_gap, h = hinge_length + 2);
        }
        plate(knuckle_r + side_gap, leaf_width, 0, hinge_length);
        difference() {
            plate(knuckle_r - 1, knuckle_r + side_gap + 0.1, split + clearance, hinge_length);
            below_cone(clearance);
        }
    }
    holes(1);
}
