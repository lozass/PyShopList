import sqlite3
from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from tkinter import messagebox, simpledialog

@dataclass
class Item:
    id: Optional[int]
    quantity: int
    description: str
    barcode: Optional[str]
    last_price: Optional[float]
    to_purchase: bool

class ShoppingList:
    def __init__(self, db_name='shopping_list.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quantity INTEGER,
                description TEXT,
                barcode TEXT UNIQUE,
                last_price REAL,
                to_purchase BOOLEAN
            )
        ''')
        self.conn.commit()

    def add_item(self, item: Item):
        self.cursor.execute('''
            INSERT INTO items (quantity, description, barcode, last_price, to_purchase)
            VALUES (?, ?, ?, ?, ?)
        ''', (item.quantity, item.description, item.barcode or None, item.last_price, item.to_purchase))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_items(self):
        self.cursor.execute('SELECT id, quantity, description, barcode, last_price, to_purchase FROM items')
        return [Item(*row) for row in self.cursor.fetchall()]

    def get_item_by_id(self, item_id: int):
        self.cursor.execute('SELECT id, quantity, description, barcode, last_price, to_purchase FROM items WHERE id = ?', (item_id,))
        row = self.cursor.fetchone()
        return Item(*row) if row else None

    def update_item(self, item_id: int, **kwargs):
        set_clause = ', '.join(f'{key} = ?' for key in kwargs)
        values = list(kwargs.values()) + [item_id]
        self.cursor.execute(f'''
            UPDATE items
            SET {set_clause}
            WHERE id = ?
        ''', values)
        self.conn.commit()

    def delete_item(self, item_id: int):
        self.cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        self.conn.commit()

    def get_items_to_purchase(self):
        self.cursor.execute('SELECT id, quantity, description, barcode, last_price, to_purchase FROM items WHERE to_purchase = 1')
        return [Item(*row) for row in self.cursor.fetchall()]

    def __del__(self):
        self.conn.close()

class ShoppingListGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Shopping List")
        self.shopping_list = ShoppingList()
        self.show_all_items = False

        # Define colors
        self.bg_color = self.master.cget('bg')  # Get the default background color
        self.active_bg = self.bg_color
        self.inactive_bg = 'SystemButtonFace'  # Default button color

        # Define monospaced font
        self.mono_font = ("Courier", 10)
        self.mono_font_bold = ("Courier", 10, "bold")

        # Create widgets
        self.create_widgets()

        # Adjust window size
        self.master.update()  # Ensure the window has been drawn
        current_width = self.master.winfo_width()
        current_height = self.master.winfo_height()
        new_width = int(current_width * 1.2)  # Increase width by 20%
        self.master.geometry(f"{new_width}x{current_height}")

    def create_widgets(self):
        # Main Menu
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # Add menu items
        self.menu_bar.add_command(label="Items to Purchase", command=self.show_to_purchase_view)
        self.menu_bar.add_command(label="Show Database Items", command=self.show_all_items_view)

        # Update menu colors
        self.update_menu_colors()

        # Frames
        self.all_items_frame = tk.Frame(self.master)
        self.to_purchase_frame = tk.Frame(self.master)

        # Add padding to both frames
        for frame in (self.all_items_frame, self.to_purchase_frame):
            left_padding = tk.Frame(frame, width=19)  # 19 pixels is approximately 0.5 cm
            left_padding.pack(side=tk.LEFT, fill=tk.Y)

            content_frame = tk.Frame(frame)
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            right_padding = tk.Frame(frame, width=19)  # 19 pixels is approximately 0.5 cm
            right_padding.pack(side=tk.RIGHT, fill=tk.Y)

            # Add top padding
            top_padding = tk.Frame(content_frame, height=19)  # 19 pixels is approximately 0.5 cm
            top_padding.pack(side=tk.TOP, fill=tk.X)

            bottom_padding = tk.Frame(content_frame, height=19)  # 19 pixels is approximately 0.5 cm
            bottom_padding.pack(side=tk.BOTTOM, fill=tk.X)

            list_frame = tk.Frame(content_frame)
            list_frame.pack(fill=tk.BOTH, expand=True)

            # Add header label for both views
            header_label = tk.Label(list_frame, text="ID | Quantity | Description           | Status", 
                                    anchor="w", bg="lightgray", font=self.mono_font_bold)
            header_label.pack(fill=tk.X, padx=(0, 16))  # Add right padding to account for scrollbar width

            # Increase listbox width by 20%
            listbox_width = int(60 * 1.2)  # Assuming original width was 50, increase by 20%
            listbox = tk.Listbox(list_frame, width=listbox_width, font=self.mono_font)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
            scrollbar.config(command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.config(yscrollcommand=scrollbar.set)
            setattr(self, f'item_listbox_{frame.winfo_name()}', listbox)

            if frame == self.all_items_frame:
                # Add Item Frame (only in all items view)
                add_frame = tk.LabelFrame(content_frame, text="Add New Item", padx=10, pady=10, relief=tk.GROOVE, borderwidth=2)
                add_frame.pack(pady=10, fill=tk.X)

                tk.Label(add_frame, text="Description:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
                self.description_entry = tk.Entry(add_frame)
                self.description_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

                tk.Label(add_frame, text="Quantity:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
                self.quantity_entry = tk.Entry(add_frame)
                self.quantity_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

                tk.Label(add_frame, text="Barcode (optional):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
                self.barcode_entry = tk.Entry(add_frame)
                self.barcode_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

                add_frame.grid_columnconfigure(1, weight=1)

                # Add Item button
                tk.Button(add_frame, text="Add Item", command=self.add_item).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

            # Buttons Frame (in both views)
            button_frame = tk.Frame(content_frame)
            button_frame.pack(side=tk.BOTTOM, pady=10, fill=tk.X)
            tk.Button(button_frame, text="Delete Item", command=self.delete_item).pack(fill=tk.X, pady=5)
            tk.Button(button_frame, text="Toggle Purchase", command=self.toggle_purchase).pack(fill=tk.X, pady=5)

        self.show_to_purchase_view()  # Start with the "Items to Purchase" view

    def show_to_purchase_view(self):
        self.show_all_items = False
        self.all_items_frame.pack_forget()
        self.to_purchase_frame.pack()
        self.update_list()
        self.update_menu_colors()

    def show_all_items_view(self):
        self.show_all_items = True
        self.to_purchase_frame.pack_forget()
        self.all_items_frame.pack()
        self.update_list()
        self.update_menu_colors()

    def update_menu_colors(self):
        # Update menu item colors based on the active view
        for index in range(2):
            is_active = (index == 0 and not self.show_all_items) or (index == 1 and self.show_all_items)
            bg_color = self.active_bg if is_active else self.inactive_bg
            
            # Update background color
            self.menu_bar.entryconfig(index, background=bg_color)

    def add_item(self):
        description = self.description_entry.get()
        quantity = self.quantity_entry.get()
        barcode = self.barcode_entry.get()

        if not description or not quantity:
            messagebox.showerror("Error", "Description and Quantity are required.")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number.")
            return

        item = Item(None, quantity, description, barcode, None, True)
        self.shopping_list.add_item(item)
        self.update_list()
        self.clear_entries()

    def update_list(self):
        current_listbox = getattr(self, f'item_listbox_{self.all_items_frame.winfo_name() if self.show_all_items else self.to_purchase_frame.winfo_name()}')
        current_listbox.delete(0, tk.END)
        
        if self.show_all_items:
            items = self.shopping_list.get_all_items()
        else:
            items = self.shopping_list.get_items_to_purchase()
        
        for item in items:
            status = "To Purchase" if item.to_purchase else "Not to Purchase"
            current_listbox.insert(tk.END, f"{item.id:2} | {item.quantity:8} | {item.description:<20} | {status}")

    def clear_entries(self):
        self.description_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.barcode_entry.delete(0, tk.END)

    def delete_item(self):
        current_listbox = getattr(self, f'item_listbox_{self.all_items_frame.winfo_name() if self.show_all_items else self.to_purchase_frame.winfo_name()}')
        selection = current_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an item to delete.")
            return

        item_id = int(current_listbox.get(selection[0]).split(':')[0])
        self.shopping_list.delete_item(item_id)
        self.update_list()

    def toggle_purchase(self):
        current_listbox = getattr(self, f'item_listbox_{self.all_items_frame.winfo_name() if self.show_all_items else self.to_purchase_frame.winfo_name()}')
        selection = current_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select an item to toggle purchase status.")
            return

        item_id = int(current_listbox.get(selection[0]).split(':')[0])
        item = self.shopping_list.get_item_by_id(item_id)
        self.shopping_list.update_item(item_id, to_purchase=not item.to_purchase)
        self.update_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = ShoppingListGUI(root)
    root.mainloop()



