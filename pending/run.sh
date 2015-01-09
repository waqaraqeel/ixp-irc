#!/bin/bash

cd /home/wirate/pyretic/pyretic/hispar/scripts

tab=" --tab-with-profile=Default"
options=()

cmds[1]="./sdx-setup.sh init hispar && ./sdx-setup.sh pyretic"
titles[1]="controller"

cmds[2]="sleep 2 && echo $1 | sudo -S true && sudo python /home/wirate/pyretic/pyretic/hispar/examples/hispar/mininet/sdx_mininext.py"
titles[2]="mininet"

cmds[3]="sleep 5 && ./sdx-setup.sh exabgp"
titles[3]="exabgp"


for i in 1 2; do
  options+=($tab --title="${titles[i]}"  -e "bash -c \"${cmds[i]} ; bash\"" )          
done

gnome-terminal "${options[@]}"
