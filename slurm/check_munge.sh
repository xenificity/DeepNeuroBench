nodes=(vm0 vm1 vm2 vm3)
for node in ${nodes[@]};do echo $node;ssh $node sudo munge -n | unmunge ;done
