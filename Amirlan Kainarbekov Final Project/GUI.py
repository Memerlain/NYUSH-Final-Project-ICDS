#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import select
from tkinter import *
from tkinter import font
from chat_utils import *
import json
import os
import sys
from queue import Queue
from PIL import Image, ImageTk, ImageDraw
import uuid
import chat_group



# GUI class for the chat
class GUI:
    # Constructor method
    def __init__(self, send, recv, sm, s):
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.counter = 0
        self.name = ""
        # Paths for images
        self.image_path = "./assets/images/"
        self.icons = {
            "menu": ImageTk.PhotoImage(Image.open(os.path.join(self.image_path, "menu.png")).resize((71, 71))),
            "peer": ImageTk.PhotoImage(Image.open(os.path.join(self.image_path, "peer.png")).resize((71, 71))),
            "group": ImageTk.PhotoImage(Image.open(os.path.join(self.image_path, "group.png")).resize((71, 71))),
            "search": ImageTk.PhotoImage(Image.open(os.path.join(self.image_path, "search.png")).resize((40, 40))),
        }
        self.current_icon = self.icons["menu"]


    # Login window
    def login(self):
        self.login = Toplevel()
        self.login.title("Login")
        self.login.resizable(width=False, height=False)
        self.login.configure(width=400, height=300)



        self.labelName = Label(self.login, text="Name: ", font="Helvetica 12")
        self.labelName.place(relheight=0.2, relx=0.1, rely=0.2)

        self.entryName = Entry(self.login, font="Helvetica 14")
        self.entryName.place(relwidth=0.4, relheight=0.12, relx=0.35, rely=0.2)
        self.entryName.focus()

        self.go = Button(self.login, text="CONTINUE", font="Helvetica 14 bold",
                         command=lambda: self.goAhead(self.entryName.get()))
        self.go.place(relx=0.4, rely=0.55)
        self.Window.mainloop()

    def update_header(self):
            """
            Update the header icon based on the peer's chat status.
            
            Parameters:
            peer_name (str): The name of the peer to check the status for.
            """
            # Check the peer's status in the chat group
            connected_peer = self.sm.peer  # Get the current peer from ClientSM
            
            if connected_peer:  # Connected in a group
                self.chat_with_label.config(text=f"Group chat")
                self.current_icon = self.icons["group"]
                self.chat_icon_label.config(image=self.icons["group"])  
            else:  # Not connected
                self.chat_with_label.config(text="Menu")
                self.current_icon = self.icons["menu"]
                self.chat_icon_label.config(image=self.icons["menu"])

                # Update the GUI to reflect the new icon



    # Proceed after login
    def goAhead(self, name):
        if len(name) > 0:
            msg = json.dumps({"action": "login", "name": name})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                print("Login successful")
                self.login.destroy()
                self.name = name
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.add_message_bubble("Welcome to the chatroom!", position="left")
                self.add_message_bubble(menu, position="left")

                # Start the proc method in a background thread
                threading.Thread(target=self.proc, daemon=True).start()
            else:
                print("Login failed")
    

    def layout(self, name):         
        self.name = name
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False, height=False)
        self.Window.configure(width=1000, height=700, bg="#C9E4FB")


        # Chat icon (left side)
        self.chat_icon_label = Label(self.Window, image=self.current_icon, bg="#6E00FF")
        self.chat_icon_label.place(x=481, y=24, width=91, height=71)

        # Chat label (right side)
        self.chat_with_label = Label(self.Window, text="Menu", font="Helvetica 16 bold", bg="#6E00FF", fg="white", justify="left")
        self.chat_with_label.place(x=572, y=24, width=409, height=71)

        # Create a canvas for the left purple bar
        self.nav_canvas = Canvas(self.Window, width=100, height=650, bg="#C9E4FB", highlightthickness=0)
        self.nav_canvas.place(x=20, y=30)
        self.nav_canvas.create_oval(0, 0, 50, 50, fill="#6E00FF", outline="#6E00FF")
        self.nav_canvas.create_oval(50, 0, 100, 50, fill="#6E00FF", outline="#6E00FF")
        self.nav_canvas.create_oval(0, 600, 50, 650, fill="#6E00FF", outline="#6E00FF")
        self.nav_canvas.create_oval(50, 600, 100, 650, fill="#6E00FF", outline="#6E00FF")
        self.nav_canvas.create_rectangle(25, 0, 75, 650, fill="#6E00FF", outline="#6E00FF")
        self.nav_canvas.create_rectangle(0, 25, 100, 625, fill="#6E00FF", outline="#6E00FF")

        # Function to create a rounded button
        def create_nav_button(parent, y, text, command):
            button_width, button_height, radius = 60, 60, 25
            canvas = Canvas(parent, width=button_width, height=button_height, bg="#6E00FF", highlightthickness=0)
            canvas.place(x=20, y=y)

            # Draw rounded rectangle
            canvas.create_oval(0, 0, radius * 2, radius * 2, fill="#6A0DAD", outline="")  # Top-left
            canvas.create_oval(button_width - radius * 2, 0, button_width, radius * 2, fill="#6A0DAD", outline="")  # Top-right
            canvas.create_oval(0, button_height - radius * 2, radius * 2, button_height, fill="#6A0DAD", outline="")  # Bottom-left
            canvas.create_oval(button_width - radius * 2, button_height - radius * 2, button_width, button_height, fill="#6A0DAD", outline="")  # Bottom-right
            canvas.create_rectangle(radius, 0, button_width - radius, button_height, fill="#6A0DAD", outline="")
            canvas.create_rectangle(0, radius, button_width, button_height - radius, fill="#6A0DAD", outline="")

            # Add button text
            button_text = canvas.create_text(button_width // 2, button_height // 2, text=text, fill="white", font="Helvetica 10 bold")

            # Bind the button click event
            canvas.bind("<Button-1>", lambda event: command())
            canvas.tag_bind(button_text, "<Button-1>", lambda event: command())

            return canvas

        # Add 4 buttons in the left navbar
        create_nav_button(self.nav_canvas, 50, "Time", lambda: self.sendButton("time"))
        create_nav_button(self.nav_canvas, 150, "Who", lambda: self.sendButton("who"))
        create_nav_button(self.nav_canvas, 540, "Quit", lambda: self.sendButton("q"))

        # Chat Frame)
        self.chat_frame = Frame(self.Window, bg="white")
        self.chat_frame.place(x=481, y=95, width=500, height=529)

        self.chat_canvas = Canvas(self.chat_frame, bg="white", highlightthickness=0)
        self.chat_scrollbar = Scrollbar(self.chat_frame, orient=VERTICAL, command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_inner_frame = Frame(self.chat_canvas, bg="white")
        self.chat_canvas.create_window((0, 0), window=self.chat_inner_frame, anchor="nw")
        self.chat_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.chat_scrollbar.pack(side=RIGHT, fill=Y)

        self.chat_inner_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )

        # Input Frame at Bottom
        self.input_frame = Frame(self.Window, bg="white")
        self.input_frame.place(x=481, y=604, width=500, height=70)

        self.entry_canvas = Canvas(self.input_frame, width=420, height=50, bg="white", highlightthickness=0)
        self.entry_canvas.pack(side=LEFT, padx=(10, 5), pady=10)
        self.entry_canvas.create_oval(0, 0, 50, 50, fill="#C9E4FB", outline="")  # Left arc
        self.entry_canvas.create_oval(370, 0, 420, 50, fill="#C9E4FB", outline="")  # Right arc
        self.entry_canvas.create_rectangle(25, 0, 395, 50, fill="#C9E4FB", outline="")

        self.entryMsg = Entry(self.input_frame, bg="#C9E4FB", fg="#303030", font="Helvetica 12", borderwidth=0, highlightthickness=0)
        self.entry_canvas.create_window(210, 25, window=self.entryMsg, width=380, height=30)
        self.entryMsg.insert(0, "")
        self.entryMsg.bind("<Return>", lambda event: self.sendButton(self.entryMsg.get()))
        self.entryMsg.bind("<FocusIn>", lambda event: self.entryMsg.delete(0, END))

        self.send_canvas = Canvas(self.input_frame, width=50, height=50, bg="white", highlightthickness=0)
        self.send_canvas.pack(side=RIGHT, padx=(5, 10), pady=10)
        self.send_canvas.create_oval(0, 0, 50, 50, fill="#6E00FF", outline="")
        self.send_canvas.create_text(25, 25, text="➞", fill="white", font="Helvetica 14 bold")
        self.send_canvas.bind("<Button-1>", lambda event: self.sendButton(self.entryMsg.get()))


        #search bar
        self.search_bar_canvas = Canvas(self.Window, width=330, height=50, bg="#C9E4FB", highlightthickness=0)
        self.search_bar_canvas.place(x=138, y=30)

        # Draw rounded rectangle for search bar
        radius = 25
        self.search_bar_canvas.create_oval(0, 0, radius * 2, radius * 2, fill="white", outline="")  # Top-left
        self.search_bar_canvas.create_oval(330 - radius * 2, 0, 330, radius * 2, fill="white", outline="")  # Top-right
        self.search_bar_canvas.create_oval(0, 50 - radius * 2, radius * 2, 50, fill="white", outline="")  # Bottom-left
        self.search_bar_canvas.create_oval(330 - radius * 2, 50 - radius * 2, 330, 50, fill="white", outline="")  # Bottom-right
        self.search_bar_canvas.create_rectangle(radius, 0, 330 - radius, 50, fill="white", outline="")
        self.search_bar_canvas.create_rectangle(0, radius, 330, 50 - radius, fill="white", outline="")

        self.search_entry = Entry(self.Window, bg="white", fg="black", font="Helvetica 14", bd=0, highlightthickness=0)
        self.search_entry.place(x=202, y=35, width=249, height=40)
        self.search_button = Button(self.Window, bg="#FFFFFF", image=self.icons["search"], command=lambda: self.sendButton(f"? {self.search_entry.get()}"))
        self.search_button.place(x=152, y=30)

        self.search_entry.bind("<Return>", lambda event: self.sendButton(f"? {self.search_entry.get()}"))


    def wrap_text(self, text, font, max_width):
        lines = []

        # Split text by manual line breaks first
        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            if not paragraph.strip():  # If it's a manual newline (\n)
                lines.append("")  # Append an empty line to preserve spacing
                continue

            words = paragraph.split()
            current_line = ""

            for word in words:
                test_line = (current_line + " " + word).strip() if current_line else word
                if font.measure(test_line) <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)  # Save the full current line
                    current_line = word  # Start a new line with the current word

            if current_line:  # Append any remaining text in the line
                lines.append(current_line)

        print(f"Number of lines: {len(lines)}")  # Debugging output
        return lines


    def add_message_bubble(self, text, position="left"):
        if text == "You: q":
            exit()
        self.update_header()
        print(f"Adding bubble - Position: {position}, Text: '{text}'")

        # Font and settings
        message_font = font.Font(family="Helvetica", size=12)
        max_width = 400  # Maximum bubble width
        min_width = 100  # Minimum bubble width
        padding = 20  # Padding from canvas borders
        bubble_spacing = 20  # Vertical spacing between bubbles
        bottom_margin = 50  # Space reserved for input area

        # Measure text width dynamically
        text_width = message_font.measure(text) + 20  # Extra padding
        bubble_width = max(min_width, min(text_width, max_width))  # Enforce min and max width

        # Calculate bubble height dynamically
        wrap_width = bubble_width - 20  # Adjust for padding
        lines = self.wrap_text(text, message_font, wrap_width)
        bubble_height = len(lines) * 15 + 20  # Line height ~16 pixels, with padding

        # Create rounded rectangle image
        def create_rounded_image(width, height, radius, color):
            image = Image.new("RGBA", (width, height), "white")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=color)
            return ImageTk.PhotoImage(image)

        # Determine bubble color based on position
        color = "#6A0DAD" if position == "right" else "#EDEDED"
        rounded_image = create_rounded_image(bubble_width, bubble_height, radius=20, color=color)

        # Store image reference
        if not hasattr(self, "bubble_images"):
            self.bubble_images = []
        self.bubble_images.append(rounded_image)

        # Create label for the text
        bubble_label = Label(
            self.chat_canvas,
            image=rounded_image,
            compound="center",
            text=text,
            wraplength=wrap_width,
            bg="white",
            fg="white" if position == "right" else "black",
            font=message_font,
            justify=LEFT,
            padx=10, pady=5
        )

        # Calculate position
        canvas_width = self.chat_canvas.winfo_width() or 500
        x_position = canvas_width - bubble_width - padding if position == "right" else padding
        last_y = self.chat_canvas.bbox("all")[3] if self.chat_canvas.bbox("all") else 10
        current_y = last_y + bubble_spacing

        # Add bubble to canvas
        self.chat_canvas.create_window(x_position, current_y, window=bubble_label, anchor="nw")

        # Update canvas scroll region
        self.chat_canvas.configure(scrollregion=(0, 0, self.chat_canvas.winfo_width(), current_y + bubble_height + bottom_margin))
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)


    def sendButton(self, msg):
        """Send a message and update the UI."""
        msg = msg.strip()
        if msg:
            self.my_msg = msg
            self.entryMsg.delete(0, END)
            self.add_message_bubble(f"You: {msg}", position="right")

    def proc(self):
        """Continuously process incoming messages."""
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0:
                self.system_msg = self.sm.proc(self.my_msg, "")
                self.my_msg = ""
                if len(self.system_msg) > 0:
                    self.add_message_bubble(self.system_msg, position="left")
                
            if len(peer_msg) > 0:
                self.system_msg = self.sm.proc("", peer_msg)
                self.my_msg = ""
                self.add_message_bubble(self.system_msg, position="left")



    def run(self):
        self.login()
