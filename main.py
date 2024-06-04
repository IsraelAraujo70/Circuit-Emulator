"" 
import tkinter as tk
from tkinter import messagebox, simpledialog
from collections import defaultdict, deque
import math

class CircuitCalculator:
    @staticmethod
    def calculate_series_resistance(resistances):
        return sum(resistances)

    @staticmethod
    def calculate_parallel_resistance(resistances):
        return 1.0 / sum(1.0/r for r in resistances) if resistances else float('inf')

    @staticmethod
    def calculate_current(voltage, resistance):
        return voltage / resistance if resistance != 0 else float('inf')

class CircuitComponent:
    def __init__(self, canvas, x, y, type, text="", value=None):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.type = type
        self.text = text
        self.value = value
        self.id = None
        self.text_id = None
        self.connected_wires = []
        self.angle = 0
        self.simulating = False  # Adicionado para verificar se está em simulação
        self.draw()

    def draw(self):
        if self.id is not None:
            self.canvas.delete(self.id)
        if self.text_id is not None:
            self.canvas.delete(self.text_id)
        if self.type == "source":
            self.id = self.canvas.create_oval(self.x-20, self.y-20, self.x+20, self.y+20, fill="yellow")
            self.text_id = self.canvas.create_text(self.x, self.y, text=self.text)
            self.canvas.create_text(self.x - 30, self.y, text="+", font="Arial 10 bold")
            self.canvas.create_text(self.x + 30, self.y, text="-", font="Arial 10 bold")
        elif self.type == "resistor":
            self.draw_resistor()
        elif self.type == "node":
            self.id = self.canvas.create_oval(self.x-5, self.y-5, self.x+5, self.y+5, fill="black")

    def draw_resistor(self, color="red"):
        if self.id is not None:
            self.canvas.delete(self.id)
        if self.text_id is not None:
            self.canvas.delete(self.text_id)
        radians = math.radians(self.angle)
        cos_val = math.cos(radians)
        sin_val = math.sin(radians)
        points = [
            (self.x - 30 * cos_val - 10 * sin_val, self.y - 30 * sin_val + 10 * cos_val),
            (self.x + 30 * cos_val - 10 * sin_val, self.y + 30 * sin_val + 10 * cos_val),
            (self.x + 30 * cos_val + 10 * sin_val, self.y + 30 * sin_val - 10 * cos_val),
            (self.x - 30 * cos_val + 10 * sin_val, self.y - 30 * sin_val - 10 * cos_val),
        ]
        self.id = self.canvas.create_polygon(points, fill=color)
        self.text_id = self.canvas.create_text(self.x, self.y, text=f"{self.value}Ω")

    def rotate(self):
        if not self.simulating:  # Impedir a rotação durante a simulação
            self.angle = (self.angle + 15) % 360
            self.draw()

class CircuitSimulatorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Circuit Simulator")
        self.master.bind("<Control-z>", self.undo)
        self.master.bind("<Control-y>", self.redo)
        self.master.bind("<Configure>", self.on_resize)

        self.setup_menu()
        self.setup_ui()

        self.calculator = CircuitCalculator()
        self.components = []
        self.component_type = None
        self.component_text = None
        self.component_value = None
        self.drawing_wire = False
        self.start_x = None
        self.start_y = None
        self.start_component = None
        self.undo_stack = []
        self.redo_stack = []
        self.wires = []
        self.temp_wire = None
        self.simulating = False
        self.current_display = None
        self.current_values = {}
        self.parallel_groups = []
        self.wire_current_texts = []

    def setup_menu(self):
        menu_bar = tk.Menu(self.master)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_project)
        file_menu.add_command(label="Open...", command=self.open_project)
        file_menu.add_command(label="Save", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.master.config(menu=menu_bar)

    def setup_ui(self):
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.master)
        btn_frame.pack(fill=tk.X)
        btns = [
            ("Add Source", lambda: self.ask_voltage("source")),
            ("Add Wire", lambda: self.set_component_type("wire")),
            ("Add Resistor", lambda: self.set_component_type("resistor")),
            ("Add Node", lambda: self.set_component_type("node")),
            ("Check Circuit", self.check_circuit_closed),
            ("Start Simulation", self.start_simulation)
        ]
        for text, cmd in btns:
            tk.Button(btn_frame, text=text, command=cmd).pack(side=tk.LEFT)

        self.canvas = tk.Canvas(main_frame, bg='white', width=600, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_grid(20)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.current_display = self.canvas.create_text(580, 20, text="", anchor="ne", font=("Arial", 12), fill="black", tags="hud")
        self.canvas.tag_raise("hud")

    def draw_grid(self, spacing):
        self.canvas.delete("grid")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        for x in range(0, width, spacing):
            self.canvas.create_line(x, 0, x, height, fill="#ddd", tags="grid")
        for y in range(0, height, spacing):
            self.canvas.create_line(0, y, width, y, fill="#ddd", tags="grid")
        self.canvas.tag_lower("grid")

    def on_canvas_click(self, event):
        grid_x = (event.x // 20) * 20
        grid_y = (event.y // 20) * 20
        if self.component_type == "wire":
            self.handle_wire_click(grid_x, grid_y)
        elif self.component_type:
            if self.component_type == "resistor":
                self.ask_resistance()
            self.add_component(grid_x, grid_y)

    def on_right_click(self, event):
        grid_x = (event.x // 20) * 20
        grid_y = (event.y // 20) * 20
        component = self.find_component_at(grid_x, grid_y)
        if component:
            component.rotate()

    def on_mouse_move(self, event):
        if self.drawing_wire and self.component_type == "wire":
            if self.temp_wire:
                self.canvas.delete(self.temp_wire)
            end_x = (event.x // 20) * 20
            end_y = (event.y // 20) * 20
            self.temp_wire = self.canvas.create_line(self.start_x, self.start_y, end_x, end_y, fill='blue', dash=(2, 2))
        if self.simulating:
            self.display_currents_and_voltage(event.x, event.y)

    def handle_wire_click(self, grid_x, grid_y):
        if not self.drawing_wire:
            self.start_x, self.start_y = grid_x, grid_y
            self.start_component = self.find_component_at(self.start_x, self.start_y)
            if self.start_component is None:
                messagebox.showerror("Error", "No component to connect to at the starting point!")
                return
            self.drawing_wire = True
        else:
            end_component = self.find_component_at(grid_x, grid_y)
            if end_component is None:
                messagebox.showerror("Error", "No component to connect to at the ending point!")
                return
            if self.temp_wire:
                self.canvas.delete(self.temp_wire)
            self.draw_wire(self.start_x, self.start_y, grid_x, grid_y)
            self.start_component.connected_wires.append((grid_x, grid_y))
            end_component.connected_wires.append((self.start_x, self.start_y))
            self.wires.append(((self.start_x, self.start_y), (grid_x, grid_y)))
            self.drawing_wire = False

    def add_component(self, grid_x, grid_y):
        text = self.component_text if self.component_type == "source" else ""
        value = self.component_value if self.component_type == "resistor" else None
        component = CircuitComponent(self.canvas, grid_x, grid_y, self.component_type, text, value)
        self.components.append(component)
        self.component_text = None
        self.component_value = None
        self.register_action(lambda: self.undo_component(component))

    def draw_wire(self, start_x, start_y, end_x, end_y):
        wire = self.canvas.create_line(start_x, start_y, end_x, end_y, fill='black', width=2)
        self.register_action(lambda: self.canvas.delete(wire))

    def find_component_at(self, x, y):
        for component in self.components:
            if self.is_component_at(component, x, y):
                return component
        return None

    def is_component_at(self, component, x, y):
        if component.type == "source" and abs(component.x - x) <= 20 and abs(component.y - y) <= 20:
            return True
        elif component.type == "resistor" and abs(component.x - x) <= 30 and abs(component.y - y) <= 10:
            return True
        elif component.type == "node" and abs(component.x - x) <= 5 and abs(component.y - y) <= 5:
            return True
        return False

    def set_component_type(self, type):
        self.component_type = type

    def ask_voltage(self, type):
        self.component_type = type
        voltage = simpledialog.askstring("Input", "Enter the voltage for the source:", parent=self.master)
        if voltage:
            self.component_text = voltage
        else:
            self.component_type = None

    def ask_resistance(self):
        resistance = simpledialog.askstring("Input", "Enter the resistance in ohms for the resistor:", parent=self.master)
        if resistance:
            self.component_value = resistance
        else:
            self.component_type = None

    def register_action(self, action):
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo_component(self, component):
        self.canvas.delete(component.id)
        if component.text_id:
            self.canvas.delete(component.text_id)
        self.components.remove(component)

    def undo(self, event=None):
        if self.undo_stack:
            action = self.undo_stack.pop()
            action()
            self.redo_stack.append(action)

    def redo(self, event=None):
        if self.redo_stack:
            action = self.redo_stack.pop()
            action()
            self.undo_stack.append(action)

    def new_project(self):
        self.canvas.delete("all")
        self.components.clear()
        self.wires.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.draw_grid(20)

    def open_project(self):
        messagebox.showinfo("Open Project", "Open project functionality coming soon!")

    def save_project(self):
        messagebox.showinfo("Save Project", "Save project functionality coming soon!")

    def on_resize(self, event):
        self.draw_grid(20)
        for component in self.components:
            component.draw()
        self.update_hud()
        self.canvas.tag_raise("hud")

    def check_circuit_closed(self):
        if not self.wires:
            messagebox.showinfo("Circuit Check", "The circuit is not closed.")
            return False

        graph = defaultdict(list)
        for (x1, y1), (x2, y2) in self.wires:
            graph[(x1, y1)].append((x2, y2))
            graph[(x2, y2)].append((x1, y1))

        visited = set()
        start = next(iter(graph))
        queue = deque([start])

        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)

        is_closed = len(visited) == len(graph) and len(graph) > 2
        if is_closed:
            self.identify_parallel_and_series()
        messagebox.showinfo("Circuit Check", "The circuit is closed." if is_closed else "The circuit is not closed.")
        return is_closed

    def start_simulation(self):
        if not self.check_circuit_closed():
            messagebox.showerror("Error", "Cannot start simulation. The circuit is not closed.")
            return
        self.simulating = True
        for component in self.components:
            component.simulating = True
        self.simulate_circuit()

    def identify_parallel_and_series(self):
        self.parallel_groups = []
        graph = defaultdict(list)
        for (x1, y1), (x2, y2) in self.wires:
            graph[(x1, y1)].append((x2, y2))
            graph[(x2, y2)].append((x1, y1))

        def dfs(node, parent, group):
            for neighbor in graph[node]:
                if neighbor != parent and neighbor not in group:
                    group.append(neighbor)
                    dfs(neighbor, node, group)

        for component in self.components:
            if component.type == "resistor":
                group = [component]
                dfs((component.x, component.y), None, group)
                self.parallel_groups.append(group)

        for group in self.parallel_groups:
            if len(group) > 1:
                for comp in group:
                    if isinstance(comp, CircuitComponent):  # Ensure comp is a CircuitComponent
                        comp.draw_resistor(color="blue")
            else:
                group[0].draw_resistor(color="red")

    def simulate_circuit(self):
        resistors = [component for component in self.components if component.type == "resistor"]
        sources = [component for component in self.components if component.type == "source"]

        if not sources:
            messagebox.showerror("Error", "No voltage source in the circuit.")
            return

        total_voltage = sum(float(source.text) for source in sources)
        total_resistance = sum(float(resistor.value) for resistor in resistors)
        total_current = self.calculator.calculate_current(total_voltage, total_resistance)

        for component in self.components:
            if component.type == "resistor":
                current = total_current
                voltage_drop = current * float(component.value)
                self.current_values[(component.x, component.y)] = (voltage_drop, current)
                self.canvas.itemconfig(component.text_id, text=f"{component.value}Ω\n{voltage_drop:.2f}V\n{current:.9f}A")

        self.update_hud()

    def update_hud(self):
        if self.simulating:
            self.display_currents_and_voltage()
        else:
            self.canvas.itemconfig(self.current_display, text="Simulation Running")
        self.canvas.tag_raise("hud")

    def display_currents_and_voltage(self, x=None, y=None):
        # Remove previous current texts
        for text_id in self.wire_current_texts:
            self.canvas.delete(text_id)
        self.wire_current_texts.clear()

        current_index = 1
        for ((x1, y1), (x2, y2)) in self.wires:
            if (x1, y1) in self.current_values:
                current = self.current_values[(x1, y1)][1]
            elif (x2, y2) in self.current_values:
                current = self.current_values[(x2, y2)][1]
            else:
                continue

            current_text = f"I_{current_index}: {current:.9f} A"
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2
            text_id = self.canvas.create_text(mid_x + 20, mid_y, text=current_text, font=("Arial", 10), fill="blue")
            self.wire_current_texts.append(text_id)
            current_index += 1

        # If x and y are provided, update the HUD display near the cursor position
        if x is not None and y is not None:
            grid_x = (x // 20) * 20
            grid_y = (y // 20) * 20
            closest_component = self.find_component_at(grid_x, grid_y)

            if closest_component and (closest_component.x, closest_component.y) in self.current_values:
                voltage, current = self.current_values[(closest_component.x, closest_component.y)]
                display_text = f"Voltage: {voltage:.9f}V\nCurrent: {current:.9f}A"
            else:
                display_text = "No data"

            # Update the HUD display near the cursor position
            self.canvas.coords(self.current_display, x + 10, y + 10)
            self.canvas.itemconfig(self.current_display, text=display_text)
            self.canvas.tag_raise("hud")

    def on_resize(self, event):
        self.draw_grid(20)
        for component in self.components:
            component.draw()
        self.update_hud()
        self.canvas.tag_raise("hud")

def main():
    root = tk.Tk()
    app = CircuitSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
