from task1 import load_obj

model = load_obj("utah_teapot_lowpoly.obj")

print(f"Количество вершин: {len(model.vertices)}")
print(f"Количество граней: {len(model.faces)}")
print(f"Количество нормалей (vn): {len(getattr(model, 'vn_list', []))}")
print(f"Количество текстур (vt): {len(getattr(model, 'vt_list', []))}")

face = model.faces[0]
print(f"Индексы вершин первой грани: {face.indices}")
print(f"Индекс нормали первой грани: {getattr(face, 'vn_index', 'Нет')}")
print(f"Индекс текстуры первой грани: {getattr(face, 'vt_index', 'Нет')}")