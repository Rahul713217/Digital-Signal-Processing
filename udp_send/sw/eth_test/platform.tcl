# 
# Usage: To re-create this platform project launch xsct with below options.
# xsct C:\Saikat_Projects\test\sw\eth_test\platform.tcl
# 
# OR launch xsct and run below command.
# source C:\Saikat_Projects\test\sw\eth_test\platform.tcl
# 
# To create the platform in a different location, modify the -out option of "platform create" command.
# -out option specifies the output directory of the platform project.

platform create -name {eth_test}\
-hw {C:\Saikat_Projects\test\design_1_wrapper.xsa}\
-proc {psu_cortexa53_0} -os {standalone} -arch {64-bit} -fsbl-target {psu_cortexa53_0} -out {C:/Saikat_Projects/test/sw}

platform write
platform generate -domains 
platform active {eth_test}
bsp reload
bsp setlib -name lwip211 -ver 1.8
bsp write
bsp reload
catch {bsp regenerate}
bsp write
platform generate
platform generate
platform generate
