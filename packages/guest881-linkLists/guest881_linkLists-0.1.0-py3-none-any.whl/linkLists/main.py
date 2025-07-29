# -*- coding: utf-8 -*-
"""
Created on 2025/6/11 19:39
@author: guest881
"""
from linkLists import *
if __name__ == '__main__':
    print("\n=== 循环链表测试 ===")
    link_circ = LinkListsManager(CircularListNode, 'circular_link')

    # 测试1：创建循环链表
    node_x = link_circ(1)
    node_y = node_x.add_node(2)
    node_z = node_y.add_node(3)
    print(f"循环链表结构: {node_x.map_link}")  # 应输出"1->2->3->1"（循环）

    # 测试2：循环关系验证
    print(f"尾节点next指向头节点: {node_z.next.value}")  # 应输出1
    print(f"头节点next指向第二个节点: {node_x.next.value}")  # 应输出2

    # 测试3：插入节点（末尾）
    new_node = CircularListNode(link_circ.register, 4)
    node_z.insert_node(new_node, 3)
    print(f"插入后结构: {node_x.map_link}")  # 应输出"1->2->3->4->1"

    # 测试4：插入节点（中间）
    mid_node = CircularListNode(link_circ.register, 2.5)
    node_x.insert_node(mid_node, 1)
    print(f"中间插入结构: {node_x.map_link}")  # 应输出"1->2.5->2->3->4->1"

    # 测试5：截断循环链表
    node_y.cut_node()  # 截断后保留前两个节点（1和2.5）
    print(f"截断后结构: {node_x.map_link}")  # 应输出"1->2.5->1"（循环）
    print(f"截断后长度: {node_x.length}")  # 应输出2
    print("\n=== 循环链表增强测试 ===")

    # 测试6：命名冲突检测
    print("\n--- 测试命名冲突 ---")
    try:
        link1 = LinkListsManager(CircularListNode, 'same_name')
        link2 = LinkListsManager(CircularListNode, 'same_name')  # 应触发KeyError
        print("命名冲突测试: 失败（未检测到重复命名）")
    except KeyError as e:
        print(f"命名冲突测试: 通过（捕获到错误: {e}）")

    # 测试7：空值调用校验
    print("\n--- 测试空值调用 ---")
    link_circ = LinkListsManager(CircularListNode, 'null_test')
    try:
        link_circ()  # 无value参数，应触发ValueError
        print("空值调用测试: 失败（未检测到空值）")
    except ValueError as e:
        print(f"空值调用测试: 通过（捕获到错误: {e}）")

    # 测试8：单节点循环与截断
    print("\n--- 测试单节点循环 ---")
    single_link = LinkListsManager(CircularListNode, 'single_node')
    node = single_link(5)
    print(f"单节点初始结构: {node.map_link}")  # 应输出 "5"（未形成循环）

    # 手动触发循环（长度≥2时才会自动建立循环）
    node.add_node(6).cut_node()  # 先添加再截断为单节点
    print(f"单节点循环结构: {node.map_link}")  # 应输出 "5->5"
    print(f"单节点截断后长度: {node.length}")  # 应输出 1

    # 测试9：边界索引插入（头节点前/尾节点后）
    print("\n--- 测试边界索引插入 ---")
    boundary_link = LinkListsManager(CircularListNode, 'boundary_test')
    n1 = boundary_link(1)
    n2 = n1.add_node(2)
    n3 = n2.add_node(3)

    # 插入到头部前（index=0）
    head_node = CircularListNode(boundary_link.register, 0)
    n1.insert_node(head_node, 0)
    print(f"头部插入后: {n1.map_link}")  # 应输出 "0->1->2->3->0"

    # 插入到尾部后（index=4）
    tail_node = CircularListNode(boundary_link.register, 4)
    n3.insert_node(tail_node, 4)
    print(f"尾部插入后: {n1.map_link}")  # 应输出 "0->1->2->3->4->0"

    # 测试10：复杂截断与循环重建
    print("\n--- 测试复杂截断场景 ---")
    complex_link = LinkListsManager(CircularListNode, 'complex_cut')
    # 构建链表: 1->2->3->4->5->1
    c1 = complex_link(1)
    c2 = c1.add_node(2)
    c3 = c2.add_node(3)
    c4 = c3.add_node(4)
    c5 = c4.add_node(5)

    print(f"初始结构: {c1.map_link}")  # 1->2->3->4->5->1

    # 截断到第3个节点（值为3）
    c3.cut_node()
    print(f"截断到节点3: {c1.map_link}")  # 应输出 "1->2->3->1"
    print(f"截断后长度: {c1.length}")  # 应输出 3

    # 从节点2继续截断
    c2.cut_node()
    print(f"截断到节点2: {c1.map_link}")  # 应输出 "1->1"
    print(f"截断后长度: {c1.length}")  # 应输出 1

    # 测试11：跨register的节点操作（错误场景）
    print("\n--- 测试非法节点操作 ---")
    wrong_link = LinkListsManager(CircularListNode, 'wrong_register')
    wrong_node = CircularListNode(wrong_link.register, '非法节点')

    try:
        # 尝试将其他register的节点插入到当前链表
        c1.insert_node(wrong_node, 1)
        print("非法节点操作测试: 失败（未检测到跨register操作）")
    except Exception as e:
        print(f"非法节点操作测试: 通过（预期错误: {type(e).__name__}）")

    # 测试12：大数据量性能测试（1000节点）
    print("\n--- 测试大数据量性能 ---")
    big_link = LinkListsManager(CircularListNode, 'big_data')
    head = big_link(1)
    current = head

    # 构建1000节点链表
    for i in range(2, 1001):
        current = current.add_node(i)

    print(f"千节点链表长度: {head.length}")  # 应输出 1000

    # 验证循环关系（尾节点next指向头节点）
    tail = head.last_node()
    print(f"千节点尾节点指向: {tail.next.value}")  # 应输出 1

    # 快速访问中间节点（第500个）
    mid_node = head.variable_node(499)
    print(f"中间节点值: {mid_node.value}")  # 应输出 500

    print("\n=== 循环链表深度逻辑测试 ===")

    # 测试13：截断后插入新节点
    print("\n--- 测试截断后插入 ---")
    trunc_insert_link = LinkListsManager(CircularListNode, 'trunc_insert')
    t1 = trunc_insert_link(1)
    t2 = t1.add_node(2)
    t3 = t2.add_node(3)

    # 截断到t2（索引1），此时链表应为[1]，循环1->1
    t2.cut_node()
    print(f"截断后结构: {t1.map_link}")  # 应输出 "1->1"

    # 从t1继续插入新节点
    t1.add_node(2)
    print(f"截断后插入: {t1.map_link}")  # 应输出 "1->2->1"
    print(f"插入后长度: {t1.length}")  # 应输出 2

    # 测试14：连续截断操作
    print("\n--- 测试连续截断 ---")
    multi_trunc_link = LinkListsManager(CircularListNode, 'multi_trunc')
    m1 = multi_trunc_link(1)
    m2 = m1.add_node(2)
    m3 = m2.add_node(3)
    m4 = m3.add_node(4)

    print(f"初始结构: {m1.map_link}")  # 1->2->3->4->1

    # 第一次截断到m2（索引1），链表变为[1]
    m2.cut_node()
    print(f"首次截断: {m1.map_link}")  # 1->1
    print(f"首次截断长度: {m1.length}")  # 1

    # 第二次截断（在单节点上调用cut_node）
    m1.cut_node()
    print(f"二次截断: {m1.map_link}")  # None
    print(f"二次截断长度: {m1.length}")  # 0

    # 测试15：插入节点后调整循环关系
    print("\n--- 测试插入循环调整 ---")
    insert_cycle_link = LinkListsManager(CircularListNode, 'insert_cycle')
    i1 = insert_cycle_link(1)
    i2 = i1.add_node(2)
    i3 = i2.add_node(3)

    # 在末尾插入（index=3）
    i4 = CircularListNode(insert_cycle_link.register, 4)
    i3.insert_node(i4, 3)
    print(f"末尾插入: {i1.map_link}")  # 1->2->3->4->1

    # 在头部插入（index=0）
    i0 = CircularListNode(insert_cycle_link.register, 0)
    i1.insert_node(i0, 0)
    print(f"头部插入: {i1.map_link}")  # 0->1->2->3->4->0

    # 验证循环关系：i4.next应指向i0
    print(f"尾节点i4指向: {i4.next.value}")  # 应输出 0

    # 测试16：跨节点遍历与指针跳转
    print("\n--- 测试跨节点遍历 ---")
    traverse_link = LinkListsManager(CircularListNode, 'traverse_test')
    t_link = traverse_link(1)
    for i in range(2, 6):
        t_link = t_link.add_node(i)  # 构建1->2->3->4->5->1

    # 从第三个节点（值为3）开始遍历
    node3 = traverse_link.register[2]
    print(f"从节点3遍历: {node3.map_link}")  # 应输出 "1->2->3->4->5->1"

    # 验证指针跳转：node3.previous_node()应指向2
    print(f"节点3的前一个节点: {node3.previous_node().value}")  # 应输出 2

    # 测试17：register存储的链表独立性
    print("\n--- 测试链表独立性 ---")
    list1 = LinkListsManager(CircularListNode, 'list1')
    list2 = LinkListsManager(CircularListNode, 'list2')

    # 向list1添加节点
    l1_1 = list1(10)
    l1_2 = l1_1.add_node(20)

    # 向list2添加节点
    l2_1 = list2(100)
    l2_2 = l2_1.add_node(200)

    # 验证list1和list2互不影响
    print(f"list1结构: {l1_1.map_link}")  # 10->20->10
    print(f"list2结构: {l2_1.map_link}")  # 100->200->100

    # 尝试用list2的节点操作list1（应报错）
    try:
        l1_1.insert_node(l2_1, 1)
        print("链表独立性测试: 失败（未检测到跨链表操作）")
    except Exception as e:
        print(f"链表独立性测试: 通过（捕获错误: {type(e).__name__}）")

