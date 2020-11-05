def get_fields(start=[1, 100, 200], stop=[5, 110, 220]):
    reg_map = []
    if len(start) == len(stop):
        for i in range(len(start)):
            for reg_num in range(start[i], stop[i]):
                reg_map.append([reg_num, 0])
        pass
        return reg_map
    else:
        raise ValueError


def get_read_param(reg_map):
    max_len = 10
    read_queue = []
    reg_seq = []
    if reg_map:
        for i in range(len(reg_map)):
            # print(i, reg_map[i])
            if len(reg_seq) == 0:
                reg_seq = [reg_map[i]]
            elif i == len(reg_map) - 1:
                read_queue.append([reg_seq[0][0], len(reg_seq)])
                reg_seq = [reg_map[i]]
            else:
                if (reg_map[i][0] - reg_map[i-1][0]) == 1:
                    reg_seq.append(reg_map[i][0])
                    if len(reg_seq) >= max_len:
                        read_queue.append([reg_seq[0][0], len(reg_seq)])
                        reg_seq = []
                else:
                    read_queue.append([reg_seq[0][0], len(reg_seq)])
                    reg_seq = [reg_map[i]]
    return read_queue


if __name__ == '__main__':
    reg_map = get_fields()
    print(reg_map)
    print(get_read_param(reg_map))
