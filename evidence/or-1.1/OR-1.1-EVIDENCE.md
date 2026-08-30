# OR-1.1 physics-kernel hardening evidence

Scenario: `or1-reference-500km-96n-12kms`

Configuration hash: `025ca45b3ed88384e9c83da13ea8f1e087783e2e93adf04ae8cfd34cbf93a318`

Source commit at generation: `7c47c60fe3d74ce534fefd2306c1e72deb3ccb48`

Source worktree dirty at generation: `True`

The ballistic primitive uses **node stride**: stride 1 targets the next node,
stride 2 bypasses one node, and stride 3 bypasses two nodes. Failure-route rows
contain one local bypass leg plus the reported count of unaffected stride-one
legs. They do not model the whole ring as a homogeneous stride-two stream.

## Global force closure

The summed finite-node value is `N × mean L1 node reaction force`. The
continuous value is `M × (v²/r − μ/r²)`. Signed and absolute relative errors
show the finite-node convergence.

| node_count | summed_l1_node_force_n | continuous_support_force_n | signed_relative_error | absolute_relative_error |
| --- | --- | --- | --- | --- |
| 48 | 1.25224691e+07 | 1.25146269e+07 | 0.00062664 | 0.00062664 |
| 96 | 1.25165870e+07 | 1.25146269e+07 | 0.00015663 | 0.00015663 |
| 192 | 1.25151169e+07 | 1.25146269e+07 | 3.91547547e-05 | 3.91547547e-05 |
| 480 | 1.25147053e+07 | 1.25146269e+07 | 6.26466768e-06 | 6.26466768e-06 |
| 960 | 1.25146466e+07 | 1.25146269e+07 | 1.57221687e-06 | 1.57221687e-06 |
| 1920 | 1.25146318e+07 | 1.25146269e+07 | 3.93055037e-07 | 3.93055037e-07 |

## L1 node-count design space

| node_count | direct_flight_time_s | minimum_free_flight_altitude_m | active_deflection_angle_rad | l1_guide_length_per_node_m | total_l1_active_guide_length_m | node_delta_v_m_s | average_node_reaction_force_n | intersects_earth | violates_minimum_safe_altitude |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 366.32583616 | 282814.98958991 | 0.39005405 | 5727.51986373 | 57275.19863733 | 4651.03310173 | 1.26964375e+06 | false | false |
| 16 | 232.40413337 | 414376.53230419 | 0.24434836 | 3587.99011804 | 57407.84188863 | 2924.8911704 | 786585.39975374 | false | false |
| 24 | 155.76580713 | 461819.53353367 | 0.16303394 | 2393.97628907 | 57455.43093763 | 1954.24129125 | 522750.92955124 | false | false |
| 32 | 117.04314569 | 478498.67326671 | 0.122311 | 1796.00409565 | 57472.13106087 | 1466.81724975 | 391633.69016486 | false | false |
| 48 | 78.13315994 | 490435.96468665 | 0.08155761 | 1197.58486913 | 57484.07371823 | 978.42008122 | 260884.77296745 | false | false |
| 64 | 58.62730505 | 494618.67538059 | 0.06117266 | 898.25400637 | 57488.25640751 | 733.95743607 | 195609.96244225 | false | false |
| 96 | 39.09794095 | 497607.80640001 | 0.04078389 | 598.86713458 | 57491.24491951 | 489.37278103 | 130381.11500562 | false | false |
| 192 | 19.55289307 | 499401.87751504 | 0.02039258 | 299.44290822 | 57493.03837753 | 244.70674281 | 65182.90059945 | false | false |
| 480 | 7.82159663 | 499904.29708297 | 0.0081571 | 119.77820957 | 57493.54059274 | 97.88497686 | 26072.30272484 | false | false |
| 960 | 3.91082969 | 499976.07425915 | 0.00407856 | 59.88917966 | 57493.61247187 | 48.94265138 | 13036.09019131 | false | false |
| 1920 | 1.95541877 | 499994.0185444 | 0.00203928 | 29.94459912 | 57493.63031068 | 24.47134601 | 6518.03740984 | false | false |

## Local failed-node bypasses

| node_count | failure_case | failed_nodes | active_node_count | unaffected_normal_leg_count | bypass_start_node | bypass_target_node | node_stride | bypassed_node_count | local_bypass_flight_time_s | local_bypass_minimum_altitude_m | local_bypass_deflection_angle_rad | local_bypass_guide_length_m | local_bypass_delta_v_m_s | route_circulation_period_s | normal_reference_circulation_period_s | active_node_passage_frequency_hz | normal_reference_passage_frequency_hz | intersects_earth | violates_minimum_safe_altitude |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 48 | one_failed_node | 1 | 47 | 46 | 0 | 2 | 2 | 1 | 155.76580713 | 461819.53353367 | 0.16303394 | 2393.97628907 | 1954.24129125 | 3749.89116435 | 3750.3916771 | 5333.48812631 | 5332.77633964 | false | false |
| 48 | two_adjacent_failed_nodes | 1,2 | 46 | 45 | 0 | 3 | 3 | 2 | 232.40413337 | 414376.53230419 | 0.24434836 | 3587.99011804 | 2924.8911704 | 3748.39633065 | 3750.3916771 | 5335.6150833 | 5332.77633964 | false | false |
| 96 | one_failed_node | 1 | 95 | 94 | 0 | 2 | 2 | 1 | 78.13315994 | 490435.96468665 | 0.08155761 | 1197.58486913 | 978.42008122 | 3753.33960943 | 3753.40233139 | 5328.58789271 | 5328.49884829 | false | false |
| 96 | two_adjacent_failed_nodes | 1,2 | 94 | 93 | 0 | 3 | 3 | 2 | 117.04314569 | 478498.67326671 | 0.122311 | 1796.00409565 | 1466.81724975 | 3753.15165422 | 3753.40233139 | 5328.85474465 | 5328.49884829 | false | false |
| 192 | one_failed_node | 1 | 191 | 190 | 0 | 2 | 2 | 1 | 39.09794095 | 497607.80640001 | 0.04078389 | 598.86713458 | 489.37278103 | 3754.14762437 | 3754.15546956 | 5327.44100689 | 5327.42987395 | false | false |
| 192 | two_adjacent_failed_nodes | 1,2 | 190 | 189 | 0 | 3 | 3 | 2 | 58.62730505 | 494618.67538059 | 0.06117266 | 898.25400637 | 733.95743607 | 3754.1240954 | 3754.15546956 | 5327.47439663 | 5327.42987395 | false | false |
| 480 | one_failed_node | 1 | 479 | 478 | 0 | 2 | 2 | 1 | 15.64269108 | 499617.19591927 | 0.01631413 | 239.55522338 | 195.76734828 | 3754.36588011 | 3754.36638229 | 5327.13130225 | 5327.13058969 | false | false |
| 480 | two_adjacent_failed_nodes | 1,2 | 478 | 477 | 0 | 3 | 3 | 2 | 23.46278123 | 499138.71926973 | 0.02447099 | 359.32984575 | 293.64450907 | 3754.36437363 | 3754.36638229 | 5327.13343981 | 5327.13058969 | false | false |
| 960 | one_failed_node | 1 | 959 | 958 | 0 | 2 | 2 | 1 | 7.82159663 | 499904.29708297 | 0.0081571 | 119.77820957 | 97.88497686 | 3754.39643701 | 3754.39649975 | 5327.08794491 | 5327.08785588 | false | false |
| 960 | two_adjacent_failed_nodes | 1,2 | 958 | 957 | 0 | 3 | 3 | 2 | 11.73223801 | 499784.670215 | 0.01223563 | 179.66694067 | 146.82665108 | 3754.3962487 | 3754.39649975 | 5327.08821209 | 5327.08785588 | false | false |

## Rotor-element scaling at fixed total mass

| element_mass_g | total_number_of_elements | kinetic_energy_per_element_j | passage_frequency_per_node_hz | mean_element_spacing_m | simultaneous_elements_in_guide | force_per_individual_element_n | total_mean_node_force_n |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1000 | 1.00000000e+06 | 7.20000000e+07 | 266.42494241 | 45.04082798 | 13.29609515 | 9806.65 | 130381.11500562 |
| 500 | 2.00000000e+06 | 3.60000000e+07 | 532.84988483 | 22.52041399 | 26.59219031 | 4903.325 | 130381.11500562 |
| 100 | 1.00000000e+07 | 7.20000000e+06 | 2664.24942415 | 4.5040828 | 132.96095154 | 980.665 | 130381.11500562 |
| 50 | 2.00000000e+07 | 3.60000000e+06 | 5328.49884829 | 2.2520414 | 265.92190307 | 490.3325 | 130381.11500562 |
| 20 | 5.00000000e+07 | 1.44000000e+06 | 13321.24712074 | 0.90081656 | 664.80475768 | 196.133 | 130381.11500562 |
| 10 | 1.00000000e+08 | 720000 | 26642.49424147 | 0.45040828 | 1329.60951537 | 98.0665 | 130381.11500562 |
| 5 | 2.00000000e+08 | 360000 | 53284.98848295 | 0.22520414 | 2659.21903073 | 49.03325 | 130381.11500562 |
| 1 | 1.00000000e+09 | 72000 | 266424.94241473 | 0.04504083 | 13296.09515367 | 9.80665 | 130381.11500562 |

Reducing element mass reduces kinetic energy and instantaneous force per
element in direct proportion to mass. Element count, passage frequency, and
simultaneous guide occupancy rise inversely, leaving the total mean node force
unchanged for fixed total rotor mass and trajectory.
