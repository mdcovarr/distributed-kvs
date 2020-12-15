from uhashring import HashRing

# create a consistent hash ring of 3 nodes of weight 1
hr = HashRing(nodes=['a1', 'a2', 'a3'])

# get the node name for the 'coconut' key
target_node = hr.get_node('coconut')

print(target_node)

target_node = hr.get_node('mango')

print(target_node)

target_node = hr.get_node('1mango')

print(target_node)

target_node = hr.get_node('2mango')

print(target_node)


target_node = hr.get_node('3mango')

print(target_node)

print("``````````````````")
print("``````````````````")


hr = HashRing(nodes=['b1', 'b2', 'b3'])


target_node = hr.get_node('b1')
print("b1: ", target_node)


print("hr: ", hr.get_nodes())



target_node = hr.get_node('coconut')
print(target_node)

target_node = hr.get_node('mango')

print(target_node)

target_node = hr.get_node('1mango')

print(target_node)

target_node = hr.get_node('2mango')

print(target_node)


target_node = hr.get_node('3mango')

print(target_node)


print("``````````````````")
print("``````````````````")



# this becomes a 2 nodes consistent hash ring
hr.remove_node('b2')

# get the node name for the 'coconut' key
target_node = hr.get_node('coconut')

print(target_node)

target_node = hr.get_node('mango')

print(target_node)

target_node = hr.get_node('1mango')

print(target_node)

target_node = hr.get_node('2mango')

print(target_node)


target_node = hr.get_node('3mango')

print(target_node)

print("``````````````````")
# add back node2
hr.add_node('node2')


# get the node name for the 'coconut' key
target_node = hr.get_node('coconut')

print(target_node)


target_node = hr.get_node('mango')

print(target_node)

target_node = hr.get_node('1mango')

print(target_node)

target_node = hr.get_node('2mango')

print(target_node)


target_node = hr.get_node('3mango')

print(target_node)