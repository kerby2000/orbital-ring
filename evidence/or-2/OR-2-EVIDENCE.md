# OR-2 magnetic rotor and guide feasibility evidence

Scenario: `or1-reference-500km-96n-12kms`

Configuration hash: `025ca45b3ed88384e9c83da13ea8f1e087783e2e93adf04ae8cfd34cbf93a318`

Source commit at generation: `ebaa391fabe5f163998c9f99691fbf703db0b5b6`

Source worktree dirty at generation: `False`

Material registry version: `1.0.0`

OR-2 consumes accepted OR-1.1 output through an immutable `GuideDemand`. No
magnetic model calls the ballistic solver or duplicates orbital equations.
The 1000-g0 guide remains a regression point, not a fixed capability.

## Reference magnetic demand

The full bounded matrix covers N=96/960, ten element masses from 1000 g to
0.1 g, and six acceleration points. The 50-g slice is shown here.

| node_count | target_acceleration_g0 | physical_guide_length_m | force_per_element_n | net_impulse_per_element_n_s | interaction_time_s | node_mean_force_n | node_mean_force_relative_error | fidelity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 96 | 100 | 5738.64182947 | 49.03325 | 24.46863905 | 0.49905595 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 96 | 250 | 2295.45673179 | 122.583125 | 24.46863905 | 0.19962238 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 96 | 500 | 1147.72836589 | 245.16625 | 24.46863905 | 0.09981119 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 96 | 1000 | 573.86418295 | 490.3325 | 24.46863905 | 0.04990559 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 96 | 2000 | 286.93209147 | 980.665 | 24.46863905 | 0.0249528 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 96 | 5000 | 114.77283659 | 2451.6625 | 24.46863905 | 0.00998112 | 130381.11500562 | -1.11610606e-16 | M1-GUIDE-KINEMATICS |
| 960 | 100 | 573.88602488 | 49.03325 | 2.44713257 | 0.04990765 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |
| 960 | 250 | 229.55440995 | 122.583125 | 2.44713257 | 0.01996306 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |
| 960 | 500 | 114.77720498 | 245.16625 | 2.44713257 | 0.00998153 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |
| 960 | 1000 | 57.38860249 | 490.3325 | 2.44713257 | 0.00499076 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |
| 960 | 2000 | 28.69430124 | 980.665 | 2.44713257 | 0.00249538 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |
| 960 | 5000 | 11.4777205 | 2451.6625 | 2.44713257 | 0.00099815 | 13036.09019131 | 0 | M1-GUIDE-KINEMATICS |

## Length-driven guide inversion

| node_count | target_physical_guide_length_m | required_acceleration_g0 | required_force_per_50g_element_n | interaction_time_s | node_mean_force_n | mode | fidelity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 96 | 50 | 11477.28365893 | 5627.68518969 | 0.00434821 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 96 | 100 | 5738.64182947 | 2813.84259485 | 0.00869641 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 96 | 250 | 2295.45673179 | 1125.53703794 | 0.02174103 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 96 | 500 | 1147.72836589 | 562.76851897 | 0.04348206 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 96 | 1000 | 573.86418295 | 281.38425948 | 0.08696412 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 96 | 2500 | 229.54567318 | 112.55370379 | 0.2174103 | 130381.11500562 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 50 | 1147.77204975 | 562.78993858 | 0.00434822 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 100 | 573.88602488 | 281.39496929 | 0.00869644 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 250 | 229.55440995 | 112.55798772 | 0.0217411 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 500 | 114.77720498 | 56.27899386 | 0.0434822 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 1000 | 57.38860249 | 28.13949693 | 0.08696439 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |
| 960 | 2500 | 22.955441 | 11.25579877 | 0.21741098 | 13036.09019131 | length-driven | M1-GUIDE-KINEMATICS |

## Node-count scaling

| node_count | turn_angle_rad | delta_v_m_s | guide_length_at_1000g0_m | force_per_50g_element_n | net_impulse_per_50g_element_n_s | node_mean_force_n | fidelity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | 0.08155761 | 978.42008122 | 1147.59604796 | 490.3325 | 48.92100406 | 260884.77296745 | M1-GUIDE-KINEMATICS |
| 96 | 0.04078389 | 489.37278103 | 573.86418295 | 490.3325 | 24.46863905 | 130381.11500562 | M1-GUIDE-KINEMATICS |
| 192 | 0.02039258 | 244.70674281 | 286.94036425 | 490.3325 | 12.23533714 | 65182.90059945 | M1-GUIDE-KINEMATICS |
| 480 | 0.0081571 | 97.88497686 | 114.77707233 | 490.3325 | 4.89424884 | 26072.30272484 | M1-GUIDE-KINEMATICS |
| 960 | 0.00407856 | 48.94265138 | 57.38860249 | 490.3325 | 2.44713257 | 13036.09019131 | M1-GUIDE-KINEMATICS |
| 1920 | 0.00203928 | 24.47134601 | 28.69430947 | 490.3325 | 1.2235673 | 6518.03740984 | M1-GUIDE-KINEMATICS |

## Specific moment and gradient

At fixed specific magnetic moment, moment and force scale with element mass,
but `G = a/(mu/m)` does not. The 100 A m2/kg, 1000-g0 regression is:

| target_acceleration_g0 | specific_magnetic_moment_a_m2_kg | element_mass_g | magnetic_moment_a_m2 | force_per_element_n | required_gradient_t_m | recovered_acceleration_m_s2 | gradient_mass_independent_at_fixed_specific_moment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | 100 | 1000 | 100 | 9806.65 | 98.0665 | 9806.65 | true |
| 1000 | 100 | 50 | 5 | 490.3325 | 98.0665 | 9806.65 | true |
| 1000 | 100 | 0.1 | 0.01 | 0.980665 | 98.0665 | 9806.65 | true |

The complete acceleration/specific-moment/mass map is in
`specific-moment-gradient-map.csv`.

## M0 Maxwell-pressure bounds

| fidelity | field_t | magnetic_pressure_pa | field_energy_density_j_m3 | requested_force_n | ideal_interaction_area_m2 |
| --- | --- | --- | --- | --- | --- |
| M0-PRESSURE | 0.5 | 99471.83944557 | 99471.83944557 | 490.3325 | 0.00492936 |
| M0-PRESSURE | 1 | 397887.35778227 | 397887.35778227 | 490.3325 | 0.00123234 |
| M0-PRESSURE | 2 | 1.59154943e+06 | 1.59154943e+06 | 490.3325 | 0.00030808 |
| M0-PRESSURE | 5 | 9.94718394e+06 | 9.94718394e+06 | 490.3325 | 4.92935993e-05 |
| M0-PRESSURE | 10 | 3.97887358e+07 | 3.97887358e+07 | 490.3325 | 1.23233998e-05 |

These are absolute pressure/energy-density scales, never a rotor force law.

## Rotor-concept comparison

| concept | fidelity | material_identifier | element_mass_g | specific_magnetic_moment_a_m2_kg | gradient_for_1000g0_t_m | available_acceleration_at_mqxf_gradient_g0 | guide_length_at_mqxf_gradient_m | aperture_radius_m | pole_tip_field_for_1000g0_t | aperture_field_energy_per_length_j_m | demagnetization_scale_flag | source_condition_supported | loss_model_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| saturated-soft-ferromagnet | M1-FERRO | vacoflux_50 | 50 | 126.22633419 | 77.69099897 | 1706.76142352 | 336.22987668 | 0.02842596 | 2.20844118 | 2463.09947316 | not-applicable | true | classical eddy/ripple comparison; hysteresis unresolved |
| permanent-magnet-dipole | M1-PM | vacodym_902_tp | 50 | 124.60156731 | 78.70406619 | 1684.79224044 | 340.61421294 | 0.02906002 | 2.28714192 | 2760.94738199 | pole-tip-exceeds-mu0-HcJ-scale | true | temperature and demagnetization load line unresolved |
| saturated-soft-ferromagnet | M1-FERRO | tdk_n87 | 50 | 52.25860761 | 187.65616706 | 706.61146967 | 812.13539205 | 0.03375358 | 6.33406821 | 28568.35783096 | not-applicable | false | classical eddy comparison; manufacturer loss not extrapolated |
| persistent-current-REBCO-loop | M1-SCLOOP | superpower_ap_4mm | 50 | 50.26548246 | 195.09710283 | 679.66155352 | 844.33815621 | 0.0275 | 5.36517033 | 13605.43504234 | not-applicable | false | REBCO in-field Ic and external-field AC loss unresolved |

No concept is ranked as best because critical thermal, structural, control,
and loss models remain unresolved. The MQXF gradient is an external scale,
not a mass-feasibility claim.

## Aperture and field energy

| element_mass_g | required_gradient_t_m | rotor_radius_m | aperture_radius_m | navigation_floor_active | pole_tip_field_t | aperture_field_energy_per_length_j_m |
| --- | --- | --- | --- | --- | --- | --- |
| 1000 | 77.69099897 | 0.03086397 | 0.07715992 | false | 5.99463164 | 133717.61202716 |
| 500 | 77.69099897 | 0.02449675 | 0.06124187 | false | 4.75794229 | 53065.86949965 |
| 100 | 77.69099897 | 0.01432579 | 0.03581446 | false | 2.78246153 | 6206.62174843 |
| 50 | 77.69099897 | 0.01137038 | 0.02842596 | false | 2.20844118 | 2463.09947316 |
| 20 | 77.69099897 | 0.00837777 | 0.02094443 | false | 1.62719337 | 725.93088347 |
| 10 | 77.69099897 | 0.00664944 | 0.0166236 | false | 1.29150424 | 288.08586202 |
| 5 | 77.69099897 | 0.00527766 | 0.01319416 | false | 1.02506759 | 114.32695011 |
| 1 | 77.69099897 | 0.0030864 | 0.00771599 | false | 0.59946316 | 13.3717612 |
| 0.5 | 77.69099897 | 0.00244967 | 0.00612419 | false | 0.47579423 | 5.30658695 |
| 0.1 | 77.69099897 | 0.00143258 | 0.005 | true | 0.38845499 | 2.35777005 |

The gradient stays fixed for the common Fe-Co specific moment. Smaller rotors
reduce aperture, pole-tip field, and ideal aperture energy until the 5-mm
navigation floor becomes active.

## Longitudinal ripple and loss

| material_identifier | longitudinal_pitch_m | ripple_frequency_hz | ripple_flux_density_amplitude_t | skin_depth_m | thickness_to_skin_depth_ratio | classical_eddy_loss_density_w_m3 | thin_section_valid | source_frequency_domain_supported |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vacoflux_50 | 10 | 1149.89950153 | 0.01 | 0.00961867 | 0.10396452 | 517.86788079 | true | not-modeled |
| vacoflux_50 | 1 | 11498.99501533 | 0.01 | 0.00304169 | 0.32876469 | 51786.78807884 | false | not-modeled |
| vacoflux_50 | 0.1 | 114989.95015331 | 0.01 | 0.00096187 | 1.03964523 | 5.17867881e+06 | false | not-modeled |
| tdk_n87 | 10 | 1149.89950153 | 0.01 | 1.00064228 | 0.00049968 | 5.43761275e-06 | true | false |
| tdk_n87 | 1 | 11498.99501533 | 0.01 | 0.31643087 | 0.00158012 | 0.00054376 | true | false |
| tdk_n87 | 0.1 | 114989.95015331 | 0.01 | 0.10006423 | 0.00499679 | 0.05437613 | true | true |
| superpower_ap_4mm | 10 | 1149.89950153 | 0.01 | not-modeled | not-modeled | not-modeled | not-modeled | false |
| superpower_ap_4mm | 1 | 11498.99501533 | 0.01 | not-modeled | not-modeled | not-modeled | not-modeled | false |
| superpower_ap_4mm | 0.1 | 114989.95015331 | 0.01 | not-modeled | not-modeled | not-modeled | not-modeled | false |

## Conductive R-L loop benchmark

| conductor_identifier | ripple_frequency_hz | resistance_ohm | inductance_h | induced_emf_amplitude_v | current_amplitude_a | average_joule_power_w | loop_formula_valid |
| --- | --- | --- | --- | --- | --- | --- | --- |
| copper_c10810 | 1149.89950153 | 0.000684 | 1.49667148e-08 | 0.00567453 | 8.19432267 | 0.02296425 | true |
| copper_c10810 | 11498.99501533 | 0.000684 | 1.49667148e-08 | 0.05674527 | 44.34884099 | 0.67265234 | true |
| copper_c10810 | 114989.95015331 | 0.000684 | 1.49667148e-08 | 0.56745266 | 52.37165579 | 0.93803429 | true |
| aluminum_1050_o | 1149.89950153 | 0.001124 | 1.49667148e-08 | 0.00567453 | 5.02530889 | 0.0141926 | true |
| aluminum_1050_o | 11498.99501533 | 0.001124 | 1.49667148e-08 | 0.05674527 | 36.38194666 | 0.74388908 | true |
| aluminum_1050_o | 114989.95015331 | 0.001124 | 1.49667148e-08 | 0.56745266 | 52.19511282 | 1.53107335 | true |

The smooth transverse gradient is separate from longitudinal ripple. Detailed
REBCO external-field AC loss remains explicitly unresolved.

## Small-element packing and coupling

| element_mass_g | kinetic_energy_per_element_j | force_per_element_at_1000g0_n | required_gradient_at_1000g0_t_m | guide_frame_spacing_m | rotor_diameter_m | packing_ratio | infeasible_overlap | aperture_radius_m | navigation_floor_active | pole_tip_field_t | neighbor_force_fraction_of_guide | separation_to_diameter_ratio | point_dipole_valid |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | 7.20000000e+07 | 9806.65 | 77.69099897 | 43.1603547 | 0.06172794 | 0.0014302 | false | 0.07715992 | false | 5.99463164 | 2.80925067e-13 | 699.20290228 | true |
| 500 | 3.60000000e+07 | 4903.325 | 77.69099897 | 21.58017735 | 0.0489935 | 0.0022703 | false | 0.06124187 | false | 4.75794229 | 2.24740054e-12 | 440.47022736 | true |
| 100 | 7.20000000e+06 | 980.665 | 77.69099897 | 4.31603547 | 0.02865157 | 0.0066384 | false | 0.03581446 | false | 2.78246153 | 2.80925067e-10 | 150.6386988 | true |
| 50 | 3.60000000e+06 | 490.3325 | 77.69099897 | 2.15801773 | 0.02274077 | 0.0105378 | false | 0.02842596 | false | 2.20844118 | 2.24740054e-09 | 94.89643378 | true |
| 20 | 1.44000000e+06 | 196.133 | 77.69099897 | 0.86320709 | 0.01675554 | 0.0194108 | false | 0.02094443 | false | 1.62719337 | 3.51156334e-08 | 51.51771032 | true |
| 10 | 720000.00000001 | 98.0665 | 77.69099897 | 0.43160355 | 0.01329888 | 0.03081273 | false | 0.0166236 | false | 1.29150424 | 2.80925067e-07 | 32.45412384 | true |
| 5 | 360000.00000001 | 49.03325 | 77.69099897 | 0.21580177 | 0.01055533 | 0.04891215 | false | 0.01319416 | false | 1.02506759 | 2.24740054e-06 | 20.44481689 | true |
| 1 | 72000 | 9.80665 | 77.69099897 | 0.04316035 | 0.00617279 | 0.14302 | false | 0.00771599 | false | 0.59946316 | 0.00028093 | 6.99202902 | true |
| 0.5 | 36000 | 4.903325 | 77.69099897 | 0.02158018 | 0.00489935 | 0.2270301 | false | 0.00612419 | false | 0.47579423 | 0.0022474 | 4.40470227 | false |
| 0.1 | 7200 | 0.980665 | 77.69099897 | 0.00431604 | 0.00286516 | 0.66384004 | true | 0.005 | true | 0.38845499 | 0.28092507 | 1.50638699 | false |

Smaller elements reduce per-element force and kinetic energy, but increase
frequency and reduce spacing. Gradient remains mass-independent at fixed
specific moment; the navigation floor limits aperture benefits, while packing
and neighbor coupling eventually worsen. Point-dipole rows outside their
separation validity domain are warnings, not trusted predictions.

## Source registry

The complete flattened registry is in `source-registry.csv`; human-readable
source boundaries are documented in `MAGNETIC_SOURCES.md`.

## Remaining limits and OR-3 recommendation

OR-2 omits 3-D FEM, real coil/yoke geometry, stress support, finite guide ends,
detailed REBCO in-field current and AC loss, persistent joints, cryogenics,
quench protection, thermal rejection, magnet/rotor fatigue, active alignment,
navigation dynamics, collective stream dynamics, and global optimization.

OR-3 should validate one or two non-ranked concept envelopes with a 2-D/3-D
field-and-force model, measured in-field material curves, thermal/loss budgets,
mechanical stress/containment, finite-length end fields, and a local
alignment/navigation controller before any system-level optimization.
