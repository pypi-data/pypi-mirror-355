class Node:
    def __init__(self, data):
        """Initialize a node with data and pointers to the next and previous nodes.
        
        Args:
            data: Data to be stored in the node
        Raises:
            ValueError: If data is None
        """
        if data is None:
            raise ValueError("Node data cannot be None")
        self.data = data
        self.next = None
        self.prev = None

class DoublyLinkedList:
    def __init__(self):
        """Initialize an empty doubly linked list."""
        self.head = None
        self.tail = None
        self._size = 0

    def is_empty(self) -> bool:
        """Check if the linked list is empty.
        
        Returns:
            bool: True if empty, False otherwise
        """
        return self.head is None

    def length(self) -> int:
        """Get the number of nodes in the linked list.
        
        Returns:
            int: Number of nodes
        """
        return self._size

    def append(self, data) -> None:
        """Append a new node with the given data to the end of the linked list.
        
        Args:
            data: Data to be appended
        Raises:
            ValueError: If data is None
        """
        new_node = Node(data)
        self._size += 1
        if not self.head:
            self.head = self.tail = new_node
            return
        new_node.prev = self.tail
        self.tail.next = new_node
        self.tail = new_node

    def display(self) -> None:
        """Display the linked list forward."""
        if self.is_empty():
            print("None")
            return
        current = self.head
        while current:
            print(current.data, end=" <-> ")
            current = current.next
        print("None")

    def __str__(self) -> str:
        """Return string representation of the linked list.
        
        Returns:
            str: String representation
        """
        if self.is_empty():
            return "None"
        elements = []
        current = self.head
        while current:
            elements.append(str(current.data))
            current = current.next
        return " <-> ".join(elements) + " <-> None"

    def insert_at_beginning(self, data) -> None:
        """Insert a new node at the beginning of the linked list.
        
        Args:
            data: Data to be inserted
        Raises:
            ValueError: If data is None
        """
        new_node = Node(data)
        self._size += 1
        if not self.head:
            self.head = self.tail = new_node
            return
        new_node.next = self.head
        self.head.prev = new_node
        self.head = new_node

    def insert_at_end(self, data) -> None:
        """Insert a new node at the end of the linked list.
        
        Args:
            data: Data to be inserted
        """
        self.append(data)

    def insert_at_position(self, position: int, data) -> None:
        """Insert a new node at a specific position (0-based index).
        
        Args:
            position: Position to insert at (0-based)
            data: Data to be inserted
        Raises:
            ValueError: If position is invalid or data is None
        """
        if position < 0 or position > self._size:
            raise ValueError(f"Invalid position: {position}")
        if position == 0:
            self.insert_at_beginning(data)
            return
        if position == self._size:
            self.append(data)
            return
        new_node = Node(data)
        self._size += 1
        current = self.head
        for _ in range(position - 1):
            current = current.next
        new_node.next = current.next
        new_node.prev = current
        current.next.prev = new_node
        current.next = new_node

    def delete_at_beginning(self) -> None:
        """Delete the node at the beginning of the linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self._size -= 1
        if self.head == self.tail:
            self.head = self.tail = None
            return
        self.head = self.head.next
        self.head.prev = None

    def delete_at_end(self) -> None:
        """Delete the node at the end of the linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self._size -= 1
        if self.head == self.tail:
            self.head = self.tail = None
            return
        self.tail = self.tail.prev
        self.tail.next = None

    def delete_at_position(self, position: int) -> None:
        """Delete the node at a specific position (0-based index).
        
        Args:
            position: Position to delete at (0-based)
        Raises:
            ValueError: If position is invalid or list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        if position < 0 or position >= self._size:
            raise ValueError(f"Invalid position: {position}")
        if position == 0:
            self.delete_at_beginning()
            return
        if position == self._size - 1:
            self.delete_at_end()
            return
        self._size -= 1
        current = self.head
        for _ in range(position - 1):
            current = current.next
        current.next = current.next.next
        current.next.prev = current

    def search(self, data) -> int:
        """Search for a node with given data and return its position.
        
        Args:
            data: Data to search for
        Returns:
            int: Position (0-based) if found, -1 if not found
        Raises:
            ValueError: If data is None
        """
        if data is None:
            raise ValueError("Search data cannot be None")
        current = self.head
        position = 0
        while current:
            if current.data == data:
                return position
            current = current.next
            position += 1
        return -1

    def reverse(self) -> None:
        """Reverse the doubly linked list."""
        if self.is_empty() or self.head == self.tail:
            return
        current = self.head
        while current:
            # Swap next and prev pointers
            temp = current.next
            current.next = current.prev
            current.prev = temp
            # Move to the next node
            current = temp
        # Swap head and tail
        temp = self.head
        self.head = self.tail
        self.tail = temp