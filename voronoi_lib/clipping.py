from voronoi_lib.point import Point

def clip_polygon(subject_polygon, clip_box):
    def inside(p, cp1, cp2):
        return (cp2.x - cp1.x) * (p.y - cp1.y) - (cp2.y - cp1.y) * (p.x - cp1.x) >= 0

    def compute_intersection(p1, p2, cp1, cp2):
        dc_x = cp1.x - cp2.x
        dc_y = cp1.y - cp2.y
        dp_x = p1.x - p2.x
        dp_y = p1.y - p2.y

        n1 = cp1.x * cp2.y - cp1.y * cp2.x
        n2 = p1.x * p2.y - p1.y * p2.x

        denom = dc_x * dp_y - dc_y * dp_x
        if abs(denom) < 1e-9:
            return None

        n3 = 1.0 / denom
        return Point((n1 * dp_x - n2 * dc_x) * n3, (n1 * dp_y - n2 * dc_y) * n3)

    output_list = subject_polygon
    cp1 = clip_box[-1]

    for clip_vertex in clip_box:
        cp2 = clip_vertex
        input_list = output_list
        output_list = []

        if not input_list:
            break

        s = input_list[-1]
        for subject_vertex in input_list:
            e = subject_vertex
            if inside(e, cp1, cp2):
                if not inside(s, cp1, cp2):
                    intersec = compute_intersection(s, e, cp1, cp2)
                    if intersec:
                        output_list.append(intersec)
                output_list.append(e)
            elif inside(s, cp1, cp2):
                intersec = compute_intersection(s, e, cp1, cp2)
                if intersec:
                    output_list.append(intersec)
            s = e
        cp1 = cp2

    return output_list
