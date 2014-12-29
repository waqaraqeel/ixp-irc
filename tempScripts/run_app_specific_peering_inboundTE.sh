cp -r ~/pyretic/pyretic/hispar/examples/app_specific_peering_inboundTE/controller/sdx_config/sdx_* ~/pyretic/pyretic/hispar
cp -r ~/pyretic/pyretic/hispar/examples/app_specific_peering_inboundTE/controller/sdx_config/bgp.conf ~/pyretic/pyretic/hispar/bgp/
./pyretic.py pyretic.hispar.main


sudo ~/pyretic/pyretic/hispar/examples/app_specific_peering_inboundTE/mininet/sdx_mininext.py


~/pyretic/pyretic/hispar/exabgp/sbin/exabgp --env ~/pyretic/pyretic/hispar/exabgp/etc/exabgp/exabgp.env ~/pyretic/pyretic/hispar/bgp/bgp.conf
