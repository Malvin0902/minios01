# Virtual Memory System Simulator

A comprehensive educational tool for understanding virtual memory management concepts through interactive visualization and simulation.

## 🎯 Features

### Core Virtual Memory Concepts
- **Complete Paging System**: Implements page tables and virtual-to-physical address translation
- **Page Fault Handling**: Demonstrates page fault detection and resolution
- **Memory Allocation Management**: Free list and bitmap tracking for memory allocation/deallocation
- **Process Management**: Create and terminate processes with automatic memory cleanup

### Page Replacement Algorithms
- **FIFO (First In, First Out)**: Simple queue-based replacement
- **LRU (Least Recently Used)**: Replaces the least recently accessed page
- **Clock Algorithm**: Circular buffer with reference bits for efficient replacement

### Interactive GUI Features
- **Real-time Physical Memory Visualization**: Color-coded frame display showing process ownership
- **Memory Allocation Bitmap**: Visual representation of allocated vs. free frames
- **Process Page Table Display**: Tree view of all processes and their page mappings
- **Performance Statistics**: Hit ratios, page fault counts, and memory utilization
- **Activity Logging**: Real-time event tracking with timestamps
- **Algorithm Comparison**: Side-by-side performance analysis

### Advanced Features
- **Address Translation**: Convert virtual addresses to physical addresses
- **Automatic Simulation Mode**: Generate random memory accesses for testing
- **Multi-Process Support**: Handle multiple processes simultaneously
- **Memory Statistics**: Comprehensive performance metrics for all algorithms

## 🚀 Getting Started

### Prerequisites
- Python 3.6 or higher
- tkinter (usually included with Python)

### Installation

1. Clone or download this repository:
```bash
git clone https://github.com/Malvin0902/minios01.git
cd minios01
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the simulator:
```bash
python os.py
```

## 📋 Usage Guide

### Basic Operations

1. **Create a Process**:
   - Enter Process ID and number of pages
   - Click "Create Process"

2. **Access Memory**:
   - Select a process and enter virtual address
   - Choose page replacement algorithm (FIFO, LRU, Clock)
   - Optionally mark as write operation
   - Click "Access Memory"

3. **Address Translation**:
   - Enter process ID and virtual address
   - Click "Translate Address" to see physical address mapping

4. **Automatic Simulation**:
   - Create one or more processes
   - Click "Start Simulation" for automated random memory accesses
   - Click "Stop Simulation" to halt

### Interface Components

#### Control Panel
- **Process Management**: Create and terminate processes
- **Memory Access**: Manual memory access with algorithm selection
- **Simulation Controls**: Start/stop automatic simulation and system reset

#### Display Areas
- **Physical Memory**: Visual representation of memory frames with process colors
- **Memory Bitmap**: Allocation status of each memory frame
- **Process Page Tables**: Hierarchical view of process page mappings
- **Statistics Panel**: Real-time performance metrics
- **Activity Log**: Chronological event history

### Example Workflow

1. Create Process 1 with 4 pages
2. Create Process 2 with 3 pages
3. Access virtual addresses (0, 4096, 8192, etc.)
4. Observe page faults and frame allocations
5. Compare different algorithm performances
6. Use "Compare Algorithms" for detailed analysis

## 🔧 System Parameters

- **Physical Frames**: 8 frames (default, configurable in code)
- **Page Size**: 4096 bytes (4KB)
- **Supported Algorithms**: FIFO, LRU, Clock
- **Maximum Processes**: Limited by available memory

## 📊 Performance Metrics

The simulator tracks comprehensive statistics:

- **Hit Ratio**: Percentage of memory accesses that result in page hits
- **Page Fault Rate**: Number of page faults per memory access
- **Memory Utilization**: Percentage of physical frames in use
- **Algorithm-specific Statistics**: Individual performance for each replacement algorithm

## 🎓 Educational Value

This simulator is designed for:

- **Operating Systems Courses**: Hands-on learning of virtual memory concepts
- **Computer Science Students**: Visual understanding of paging mechanisms
- **Algorithm Analysis**: Comparing page replacement algorithm performance
- **System Understanding**: Observing memory management in action

### Concepts Demonstrated

1. **Virtual Memory Management**
2. **Page Table Operations**
3. **Page Fault Handling**
4. **Memory Allocation Strategies**
5. **Algorithm Performance Analysis**
6. **Process Memory Isolation**

## 🛠️ Technical Details

### Architecture
- **Object-Oriented Design**: Clean separation of concerns
- **MVC Pattern**: GUI separated from core logic
- **Thread-Safe Operations**: Background simulation support
- **Modular Components**: Easy to extend and modify

### Data Structures
- **Page Class**: Represents virtual memory pages
- **Frame Class**: Represents physical memory frames
- **Process Class**: Manages process page tables
- **VirtualMemorySystem**: Core simulation engine

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

- Additional page replacement algorithms (Optimal, Second Chance)
- TLB (Translation Lookaside Buffer) simulation
- Multi-level page tables
- Segmentation support
- Performance benchmarking tools

## 📝 License

This project is open source and available under the MIT License.

## 👤 Author

**Malvin0902**
- GitHub: [@Malvin0902](https://github.com/Malvin0902)

## 🙏 Acknowledgments

- Inspired by operating system textbooks and educational resources
- Built for educational purposes to enhance understanding of virtual memory systems
- Designed to bridge the gap between theory and practical implementation

---

*This simulator provides a hands-on approach to learning virtual memory management, making complex concepts accessible through interactive visualization.*
