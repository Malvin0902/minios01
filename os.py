import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import threading

@dataclass
class Page:
    """Represents a page in virtual memory"""
    page_number: int
    process_id: int
    data: str = ""
    
@dataclass
class Frame:
    """Represents a frame in physical memory"""
    frame_number: int
    page: Optional[Page] = None
    load_time: float = 0
    last_access_time: float = 0
    reference_bit: bool = False
    dirty_bit: bool = False

class Process:
    """Represents a process with its page table"""
    def __init__(self, process_id: int, pages: int):
        self.process_id = process_id
        self.pages = pages
        self.page_table: Dict[int, Optional[int]] = {i: None for i in range(pages)}
        self.color = f"#{random.randint(0x100000, 0xFFFFFF):06x}"

class VirtualMemorySystem:
    """Core virtual memory management system"""
    
    def __init__(self, physical_frames: int = 8, page_size: int = 4096):
        self.physical_frames = physical_frames
        self.page_size = page_size
        self.frames = [Frame(i) for i in range(physical_frames)]
        self.processes: Dict[int, Process] = {}
        self.free_frames = list(range(physical_frames))
        self.current_time = 0
        
        # Statistics for different algorithms
        self.algorithm_stats = {
            "FIFO": {"page_faults": 0, "memory_accesses": 0, "hit_count": 0},
            "LRU": {"page_faults": 0, "memory_accesses": 0, "hit_count": 0},
            "Clock": {"page_faults": 0, "memory_accesses": 0, "hit_count": 0}
        }
        
        # Global statistics
        self.page_faults = 0
        self.memory_accesses = 0
        self.hit_count = 0
        
        # Page replacement algorithm state
        self.clock_hand = 0
        self.fifo_queue = deque()
        
        # Memory allocation tracking (free list/bitmap)
        self.free_list = list(range(physical_frames))
        self.allocation_bitmap = [False] * physical_frames
        
    def create_process(self, process_id: int, num_pages: int) -> bool:
        """Create a new process with specified number of pages"""
        if process_id in self.processes:
            return False
        
        self.processes[process_id] = Process(process_id, num_pages)
        return True
    
    def terminate_process(self, process_id: int) -> bool:
        """Terminate a process and free its memory"""
        if process_id not in self.processes:
            return False
        
        process = self.processes[process_id]
        
        # Free all frames used by this process - update free list and bitmap
        for frame in self.frames:
            if frame.page and frame.page.process_id == process_id:
                self.free_frames.append(frame.frame_number)
                self.free_list.append(frame.frame_number)
                self.allocation_bitmap[frame.frame_number] = False
                frame.page = None
                frame.load_time = 0
                frame.last_access_time = 0
                frame.reference_bit = False
                frame.dirty_bit = False
        
        # Sort free frames for better visualization
        self.free_frames.sort()
        self.free_list.sort()
        
        # Remove from FIFO queue
        self.fifo_queue = deque([f for f in self.fifo_queue if f.page is None or f.page.process_id != process_id])
        
        del self.processes[process_id]
        return True
    
    def access_memory(self, process_id: int, virtual_address: int, write: bool = False, algorithm: str = "FIFO") -> Tuple[bool, str]:
        """Access memory at virtual address"""
        self.current_time += 1
        self.memory_accesses += 1
        
        # Update algorithm-specific statistics
        if algorithm in self.algorithm_stats:
            self.algorithm_stats[algorithm]["memory_accesses"] += 1
        
        if process_id not in self.processes:
            return False, f"Process {process_id} does not exist"
        
        process = self.processes[process_id]
        page_number = virtual_address // self.page_size
        
        if page_number >= process.pages:
            return False, f"Virtual address {virtual_address} out of bounds for process {process_id}"
        
        # Check if page is in memory (page table lookup)
        frame_number = process.page_table[page_number]
        
        if frame_number is not None:
            # Page hit
            self.hit_count += 1
            if algorithm in self.algorithm_stats:
                self.algorithm_stats[algorithm]["hit_count"] += 1
                
            frame = self.frames[frame_number]
            frame.last_access_time = self.current_time
            frame.reference_bit = True
            if write:
                frame.dirty_bit = True
            return True, f"Page hit: Virtual address {virtual_address} -> Physical frame {frame_number}"
        else:
            # Page fault
            self.page_faults += 1
            if algorithm in self.algorithm_stats:
                self.algorithm_stats[algorithm]["page_faults"] += 1
            return self._handle_page_fault(process_id, page_number, algorithm)
    
    def _handle_page_fault(self, process_id: int, page_number: int, algorithm: str) -> Tuple[bool, str]:
        """Handle page fault using specified replacement algorithm"""
        process = self.processes[process_id]
        
        # Create new page
        new_page = Page(page_number, process_id, f"Data_{process_id}_{page_number}")
        
        if self.free_frames:
            # Use free frame - update free list and bitmap
            frame_number = self.free_frames.pop(0)
            self.free_list.remove(frame_number) if frame_number in self.free_list else None
            self.allocation_bitmap[frame_number] = True
            
            frame = self.frames[frame_number]
            frame.page = new_page
            frame.load_time = self.current_time
            frame.last_access_time = self.current_time
            frame.reference_bit = True
            frame.dirty_bit = False
            
            process.page_table[page_number] = frame_number
            self.fifo_queue.append(frame)
            
            return True, f"Page fault handled: Loaded page {page_number} of process {process_id} into frame {frame_number}"
        else:
            # Need to replace a page
            victim_frame_index = self._select_victim_page(algorithm)
            victim_frame = self.frames[victim_frame_index]
            
            # Remove old page from page table
            if victim_frame.page:
                old_process = self.processes.get(victim_frame.page.process_id)
                if old_process:
                    old_process.page_table[victim_frame.page.page_number] = None
            
            # Load new page
            victim_frame.page = new_page
            victim_frame.load_time = self.current_time
            victim_frame.last_access_time = self.current_time
            victim_frame.reference_bit = True
            victim_frame.dirty_bit = False
            
            process.page_table[page_number] = victim_frame_index
            
            return True, f"Page fault handled: Replaced frame {victim_frame_index} with page {page_number} of process {process_id}"
    
    def _select_victim_page(self, algorithm: str) -> int:
        """Select victim page for replacement based on algorithm"""
        occupied_frames = [f for f in self.frames if f.page is not None]
        
        if not occupied_frames:
            return 0
        
        if algorithm == "FIFO":
            return self._fifo_replacement()
        elif algorithm == "LRU":
            return self._lru_replacement()
        elif algorithm == "Clock":
            return self._clock_replacement()
        else:
            return 0
    
    def _fifo_replacement(self) -> int:
        """FIFO page replacement"""
        if self.fifo_queue:
            victim_frame = self.fifo_queue.popleft()
            self.fifo_queue.append(victim_frame)
            return victim_frame.frame_number
        return 0
    
    def _lru_replacement(self) -> int:
        """LRU page replacement"""
        occupied_frames = [f for f in self.frames if f.page is not None]
        if not occupied_frames:
            return 0
        
        lru_frame = min(occupied_frames, key=lambda f: f.last_access_time)
        return lru_frame.frame_number
    
    def _clock_replacement(self) -> int:
        """Clock page replacement algorithm"""
        while True:
            frame = self.frames[self.clock_hand]
            if frame.page is None:
                self.clock_hand = (self.clock_hand + 1) % len(self.frames)
                continue
                
            if not frame.reference_bit:
                victim = self.clock_hand
                self.clock_hand = (self.clock_hand + 1) % len(self.frames)
                return victim
            else:
                frame.reference_bit = False
                self.clock_hand = (self.clock_hand + 1) % len(self.frames)
    
    def get_hit_ratio(self) -> float:
        """Calculate hit ratio"""
        if self.memory_accesses == 0:
            return 0.0
        return (self.hit_count / self.memory_accesses) * 100
    
    def get_algorithm_hit_ratio(self, algorithm: str) -> float:
        """Calculate hit ratio for specific algorithm"""
        if algorithm not in self.algorithm_stats:
            return 0.0
        stats = self.algorithm_stats[algorithm]
        if stats["memory_accesses"] == 0:
            return 0.0
        return (stats["hit_count"] / stats["memory_accesses"]) * 100
    
    def get_memory_map(self) -> Dict[str, any]:
        """Get detailed memory map for visualization"""
        memory_map = {
            "frames": [],
            "free_frames": self.free_frames,
            "allocation_bitmap": self.allocation_bitmap,
            "free_list": self.free_list
        }
        
        for frame in self.frames:
            frame_info = {
                "frame_number": frame.frame_number,
                "is_free": frame.page is None,
                "process_id": frame.page.process_id if frame.page else None,
                "page_number": frame.page.page_number if frame.page else None,
                "load_time": frame.load_time,
                "last_access_time": frame.last_access_time,
                "reference_bit": frame.reference_bit,
                "dirty_bit": frame.dirty_bit
            }
            memory_map["frames"].append(frame_info)
        
        return memory_map
    
    def translate_address(self, process_id: int, virtual_address: int) -> Tuple[bool, str, int]:
        """Translate virtual address to physical address"""
        if process_id not in self.processes:
            return False, f"Process {process_id} does not exist", -1
        
        process = self.processes[process_id]
        page_number = virtual_address // self.page_size
        offset = virtual_address % self.page_size
        
        if page_number >= process.pages:
            return False, f"Virtual address {virtual_address} out of bounds", -1
        
        frame_number = process.page_table[page_number]
        if frame_number is None:
            return False, f"Page {page_number} not in memory (page fault would occur)", -1
        
        physical_address = frame_number * self.page_size + offset
        return True, f"Virtual {virtual_address} -> Physical {physical_address} (Frame {frame_number}, Offset {offset})", physical_address

class VirtualMemoryGUI:
    """GUI for Virtual Memory System Simulator"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Virtual Memory System Simulator")
        self.root.geometry("1200x800")
        
        self.vm_system = VirtualMemorySystem()
        self.is_simulation_running = False
        self.simulation_thread = None
        
        self.setup_gui()
        self.update_display()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Process management
        process_frame = ttk.Frame(control_frame)
        process_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(process_frame, text="Process ID:").pack(side=tk.LEFT)
        self.process_id_var = tk.StringVar(value="1")
        ttk.Entry(process_frame, textvariable=self.process_id_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(process_frame, text="Pages:").pack(side=tk.LEFT, padx=(10, 0))
        self.pages_var = tk.StringVar(value="4")
        ttk.Entry(process_frame, textvariable=self.pages_var, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(process_frame, text="Create Process", command=self.create_process).pack(side=tk.LEFT, padx=5)
        ttk.Button(process_frame, text="Terminate Process", command=self.terminate_process).pack(side=tk.LEFT, padx=5)
        
        # Memory access
        access_frame = ttk.Frame(control_frame)
        access_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(access_frame, text="Virtual Address:").pack(side=tk.LEFT)
        self.virtual_addr_var = tk.StringVar(value="0")
        ttk.Entry(access_frame, textvariable=self.virtual_addr_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(access_frame, text="Algorithm:").pack(side=tk.LEFT, padx=(10, 0))
        self.algorithm_var = tk.StringVar(value="FIFO")
        algorithm_combo = ttk.Combobox(access_frame, textvariable=self.algorithm_var, 
                                     values=["FIFO", "LRU", "Clock"], width=8)
        algorithm_combo.pack(side=tk.LEFT, padx=5)
        
        self.write_var = tk.BooleanVar()
        ttk.Checkbutton(access_frame, text="Write", variable=self.write_var).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(access_frame, text="Access Memory", command=self.access_memory).pack(side=tk.LEFT, padx=5)
        ttk.Button(access_frame, text="Random Access", command=self.random_access).pack(side=tk.LEFT, padx=5)
        ttk.Button(access_frame, text="Translate Address", command=self.translate_address).pack(side=tk.LEFT, padx=5)
        
        # Simulation controls
        sim_frame = ttk.Frame(control_frame)
        sim_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(sim_frame, text="Start Simulation", command=self.start_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(sim_frame, text="Stop Simulation", command=self.stop_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(sim_frame, text="Reset System", command=self.reset_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(sim_frame, text="Compare Algorithms", command=self.compare_algorithms).pack(side=tk.LEFT, padx=5)
        
        # Display area
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Physical memory and bitmap
        left_panel = ttk.Frame(display_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Physical memory display
        memory_frame = ttk.LabelFrame(left_panel, text="Physical Memory")
        memory_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.memory_canvas = tk.Canvas(memory_frame, bg="white", height=300)
        memory_scroll = ttk.Scrollbar(memory_frame, orient="vertical", command=self.memory_canvas.yview)
        self.memory_canvas.configure(yscrollcommand=memory_scroll.set)
        self.memory_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        memory_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Memory bitmap visualization
        bitmap_frame = ttk.LabelFrame(left_panel, text="Memory Allocation Bitmap")
        bitmap_frame.pack(fill=tk.X)
        
        self.bitmap_canvas = tk.Canvas(bitmap_frame, bg="white", height=80)
        self.bitmap_canvas.pack(fill=tk.X, padx=5, pady=5)
        
        # Process and statistics display
        right_frame = ttk.Frame(display_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Process table display
        process_frame = ttk.LabelFrame(right_frame, text="Process Page Tables")
        process_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.process_tree = ttk.Treeview(process_frame, columns=("Page", "Frame"), show="tree headings")
        self.process_tree.heading("#0", text="Process")
        self.process_tree.heading("Page", text="Page")
        self.process_tree.heading("Frame", text="Frame")
        self.process_tree.column("#0", width=80)
        self.process_tree.column("Page", width=60)
        self.process_tree.column("Frame", width=60)
        
        process_scroll = ttk.Scrollbar(process_frame, orient="vertical", command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=process_scroll.set)
        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        process_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Statistics display
        stats_frame = ttk.LabelFrame(right_frame, text="Statistics")
        stats_frame.pack(fill=tk.X)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log")
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=6)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_process(self):
        """Create a new process"""
        try:
            process_id = int(self.process_id_var.get())
            pages = int(self.pages_var.get())
            
            if self.vm_system.create_process(process_id, pages):
                self.log(f"Process {process_id} created with {pages} pages")
                self.update_display()
            else:
                messagebox.showerror("Error", f"Process {process_id} already exists")
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def terminate_process(self):
        """Terminate a process"""
        try:
            process_id = int(self.process_id_var.get())
            
            if self.vm_system.terminate_process(process_id):
                self.log(f"Process {process_id} terminated")
                self.update_display()
            else:
                messagebox.showerror("Error", f"Process {process_id} does not exist")
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def access_memory(self):
        """Access memory at specified virtual address"""
        try:
            process_id = int(self.process_id_var.get())
            virtual_addr = int(self.virtual_addr_var.get())
            write = self.write_var.get()
            algorithm = self.algorithm_var.get()
            
            success, message = self.vm_system.access_memory(process_id, virtual_addr, write, algorithm)
            
            if success:
                self.log(message)
            else:
                self.log(f"ERROR: {message}")
            
            self.update_display()
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def random_access(self):
        """Generate random memory access"""
        if not self.vm_system.processes:
            messagebox.showwarning("Warning", "No processes exist")
            return
        
        process_id = random.choice(list(self.vm_system.processes.keys()))
        process = self.vm_system.processes[process_id]
        virtual_addr = random.randint(0, (process.pages - 1) * self.vm_system.page_size)
        write = random.choice([True, False])
        algorithm = self.algorithm_var.get()
        
        self.virtual_addr_var.set(str(virtual_addr))
        self.process_id_var.set(str(process_id))
        self.write_var.set(write)
        
        success, message = self.vm_system.access_memory(process_id, virtual_addr, write, algorithm)
        self.log(message if success else f"ERROR: {message}")
        self.update_display()
    
    def translate_address(self):
        """Translate virtual address to physical address"""
        try:
            process_id = int(self.process_id_var.get())
            virtual_addr = int(self.virtual_addr_var.get())
            
            success, message, physical_addr = self.vm_system.translate_address(process_id, virtual_addr)
            
            if success:
                self.log(f"Address Translation: {message}")
            else:
                self.log(f"Translation Failed: {message}")
        except ValueError:
            messagebox.showerror("Error", "Invalid input")
    
    def compare_algorithms(self):
        """Show algorithm comparison window"""
        comparison_window = tk.Toplevel(self.root)
        comparison_window.title("Algorithm Performance Comparison")
        comparison_window.geometry("600x400")
        
        # Create text widget for comparison
        text_widget = tk.Text(comparison_window, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(comparison_window, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Generate comparison report
        report = "ALGORITHM PERFORMANCE COMPARISON\n"
        report += "=" * 50 + "\n\n"
        
        for algorithm in ["FIFO", "LRU", "Clock"]:
            stats = self.vm_system.algorithm_stats[algorithm]
            hit_ratio = self.vm_system.get_algorithm_hit_ratio(algorithm)
            
            report += f"{algorithm} Algorithm:\n"
            report += f"  Memory Accesses: {stats['memory_accesses']}\n"
            report += f"  Page Faults: {stats['page_faults']}\n"
            report += f"  Page Hits: {stats['hit_count']}\n"
            report += f"  Hit Ratio: {hit_ratio:.2f}%\n\n"
        
        # Overall statistics
        report += "OVERALL SYSTEM STATISTICS:\n"
        report += f"Total Memory Accesses: {self.vm_system.memory_accesses}\n"
        report += f"Total Page Faults: {self.vm_system.page_faults}\n"
        report += f"Total Page Hits: {self.vm_system.hit_count}\n"
        report += f"Overall Hit Ratio: {self.vm_system.get_hit_ratio():.2f}%\n\n"
        
        # Memory utilization
        memory_map = self.vm_system.get_memory_map()
        used_frames = len([f for f in memory_map["frames"] if not f["is_free"]])
        utilization = (used_frames / self.vm_system.physical_frames) * 100
        
        report += "MEMORY UTILIZATION:\n"
        report += f"Physical Frames: {self.vm_system.physical_frames}\n"
        report += f"Used Frames: {used_frames}\n"
        report += f"Free Frames: {len(memory_map['free_frames'])}\n"
        report += f"Utilization: {utilization:.2f}%\n"
        
        text_widget.insert(1.0, report)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def start_simulation(self):
        """Start automatic simulation"""
        if not self.is_simulation_running and self.vm_system.processes:
            self.is_simulation_running = True
            self.simulation_thread = threading.Thread(target=self.simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop automatic simulation"""
        self.is_simulation_running = False
    
    def simulation_loop(self):
        """Automatic simulation loop"""
        while self.is_simulation_running and self.vm_system.processes:
            self.root.after(0, self.random_access)
            time.sleep(1)
    
    def reset_system(self):
        """Reset the virtual memory system"""
        self.stop_simulation()
        self.vm_system = VirtualMemorySystem()
        self.log("System reset")
        self.update_display()
    
    def update_display(self):
        """Update all display components"""
        self.update_memory_display()
        self.update_bitmap_display()
        self.update_process_display()
        self.update_statistics()
    
    def update_memory_display(self):
        """Update physical memory visualization"""
        self.memory_canvas.delete("all")
        
        frame_height = 40
        frame_width = 200
        margin = 10
        
        for i, frame in enumerate(self.vm_system.frames):
            y = i * (frame_height + margin) + margin
            
            # Draw frame rectangle
            if frame.page is None:
                color = "lightgray"
                text = f"Frame {i}: Empty"
            else:
                process = self.vm_system.processes[frame.page.process_id]
                color = process.color
                text = f"Frame {i}: P{frame.page.process_id} Page {frame.page.page_number}"
            
            self.memory_canvas.create_rectangle(
                margin, y, margin + frame_width, y + frame_height,
                fill=color, outline="black", width=2
            )
            
            self.memory_canvas.create_text(
                margin + frame_width // 2, y + frame_height // 2,
                text=text, font=("Arial", 10, "bold")
            )
            
            # Show additional info
            if frame.page is not None:
                info_text = f"Loaded: {frame.load_time:.0f}, Accessed: {frame.last_access_time:.0f}"
                if frame.reference_bit:
                    info_text += ", R"
                if frame.dirty_bit:
                    info_text += ", D"
                
                self.memory_canvas.create_text(
                    margin + frame_width // 2, y + frame_height + 5,
                    text=info_text, font=("Arial", 8)
                )
        
        # Update scroll region
        self.memory_canvas.configure(scrollregion=self.memory_canvas.bbox("all"))
    
    def update_bitmap_display(self):
        """Update memory allocation bitmap visualization"""
        self.bitmap_canvas.delete("all")
        
        canvas_width = self.bitmap_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = 400
        
        frame_width = max(20, canvas_width // self.vm_system.physical_frames - 2)
        
        for i, allocated in enumerate(self.vm_system.allocation_bitmap):
            x = i * (frame_width + 2) + 5
            y = 10
            
            color = "red" if allocated else "lightgreen"
            text_color = "white" if allocated else "black"
            
            self.bitmap_canvas.create_rectangle(
                x, y, x + frame_width, y + 30,
                fill=color, outline="black", width=1
            )
            
            self.bitmap_canvas.create_text(
                x + frame_width // 2, y + 15,
                text=str(i), font=("Arial", 8, "bold"),
                fill=text_color
            )
        
        # Add legend
        legend_y = 50
        self.bitmap_canvas.create_rectangle(5, legend_y, 25, legend_y + 15, fill="lightgreen", outline="black")
        self.bitmap_canvas.create_text(35, legend_y + 7, text="Free", anchor="w", font=("Arial", 8))
        
        self.bitmap_canvas.create_rectangle(80, legend_y, 100, legend_y + 15, fill="red", outline="black")
        self.bitmap_canvas.create_text(110, legend_y + 7, text="Allocated", anchor="w", font=("Arial", 8))
    
    def update_process_display(self):
        """Update process page table display"""
        self.process_tree.delete(*self.process_tree.get_children())
        
        for process_id, process in self.vm_system.processes.items():
            process_item = self.process_tree.insert("", "end", text=f"Process {process_id}")
            
            for page_num, frame_num in process.page_table.items():
                frame_text = str(frame_num) if frame_num is not None else "Not in memory"
                self.process_tree.insert(process_item, "end", values=(page_num, frame_text))
    
    def update_statistics(self):
        """Update statistics display"""
        # Calculate memory utilization
        used_frames = self.vm_system.physical_frames - len(self.vm_system.free_frames)
        utilization = (used_frames / self.vm_system.physical_frames) * 100
        
        stats = f"""GLOBAL STATISTICS:
Memory Accesses: {self.vm_system.memory_accesses}
Page Faults: {self.vm_system.page_faults}
Page Hits: {self.vm_system.hit_count}
Hit Ratio: {self.vm_system.get_hit_ratio():.2f}%

MEMORY STATUS:
Physical Frames: {self.vm_system.physical_frames}
Free Frames: {len(self.vm_system.free_frames)}
Used Frames: {used_frames}
Utilization: {utilization:.1f}%

ALGORITHM PERFORMANCE:
FIFO Hit Ratio: {self.vm_system.get_algorithm_hit_ratio('FIFO'):.2f}%
LRU Hit Ratio: {self.vm_system.get_algorithm_hit_ratio('LRU'):.2f}%
Clock Hit Ratio: {self.vm_system.get_algorithm_hit_ratio('Clock'):.2f}%

SYSTEM INFO:
Active Processes: {len(self.vm_system.processes)}
Total Pages: {sum(p.pages for p in self.vm_system.processes.values())}
Current Algorithm: {self.algorithm_var.get()}
Current Time: {self.vm_system.current_time}
Page Size: {self.vm_system.page_size} bytes"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
    
    def log(self, message):
        """Add message to activity log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the Virtual Memory Simulator"""
    print("Virtual Memory System Simulator")
    print("=" * 40)
    print("Features:")
    print("- Complete paging system with page tables")
    print("- Virtual-to-physical address translation")
    print("- Multiple page replacement algorithms (FIFO, LRU, Clock)")
    print("- Process creation and termination with memory management")
    print("- Memory allocation/deallocation with free list and bitmap tracking")
    print("- Interactive GUI with real-time visualizations:")
    print("  * Physical memory frame visualization")
    print("  * Memory allocation bitmap display")
    print("  * Process page table contents")
    print("  * Page fault detection and handling")
    print("- Performance statistics and algorithm comparison")
    print("- Real-time activity logging")
    print("- Automatic simulation mode")
    print("- Address translation demonstration")
    print()
    print("This simulator demonstrates all core virtual memory concepts:")
    print("- Paging and page tables")
    print("- Page fault handling")
    print("- Memory allocation management")
    print("- Algorithm performance comparison")
    print()
    
    # Create and run the GUI
    app = VirtualMemoryGUI()
    app.run()

if __name__ == "__main__":
    main()