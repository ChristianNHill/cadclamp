// t2-007 funnel
$fn = 96;
inlet_diameter = 60;
outlet_diameter = 10;
wall_thickness = 1.6;
spout_od = 14;
spout_length = 20;
cone_height = 50;
cone_top_od = 63.2;

rotate_extrude()
    polygon([
        [outlet_diameter / 2, 0],
        [spout_od / 2, 0],
        [spout_od / 2, spout_length],
        [cone_top_od / 2, spout_length + cone_height],
        [inlet_diameter / 2, spout_length + cone_height],
        [outlet_diameter / 2, spout_length]
    ]);
