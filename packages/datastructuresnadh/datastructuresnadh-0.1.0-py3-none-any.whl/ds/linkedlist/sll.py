# Node class for Singly Linked List
class Node:
    def __init__(self, data):
        """Initialize a node with data and a pointer to the next node.
        
        Args:
            data: Data to be stored in the node
        Raises:
            ValueError: If data is None
        """
        if data is None:
            raise ValueError("Node data cannot be None")
        self.data = data
        self.next = None

class SinglyLinkedList:
    def __init__(self):
        """Initialize an empty singly linked list."""
        self.head = None
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
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node

    def display(self) -> None:
        """Display the linked list."""
        if self.is_empty():
            print("None")
            return
        current = self.head
        while current:
            print(current.data, end=" -> ")
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
        return " -> ".join(elements) + " -> None"

    def insert_at_beginning(self, data) -> None:
        """Insert a new node at the beginning of the linked list.
        
        Args:
            data: Data to be inserted
        Raises:
            ValueError: If data is None
        """
        new_node = Node(data)
        self._size += 1
        new_node.next = self.head
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
        new_node = Node(data)
        self._size += 1
        if position == 0:
            new_node.next = self.head
            self.head = new_node
            return
        current = self.head
        for _ in range(position - 1):
            current = current.next
        new_node.next = current.next
        current.next = new_node

    def delete_at_beginning(self) -> None:
        """Delete the node at the beginning of the linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self.head = self.head.next
        self._size -= 1

    def delete_at_end(self) -> None:
        """Delete the node at the end of the linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self._size -= 1
        if not self.head.next:
            self.head = None
            return
        current = self.head
        while current.next.next:
            current = current.next
        current.next = None

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
        self._size -= 1
        if position == 0:
            self.head = self.head.next
            return
        current = self.head
        for _ in range(position - 1):
            current = current.next
        current.next = current.next.next

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
        """Reverse the singly linked list."""
        prev = None
        current = self.head
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.head = prev

class CircularSinglyLinkedList:
    def __init__(self):
        """Initialize an empty circular singly linked list."""
        self.head = None
        self._size = 0

    def is_empty(self) -> bool:
        """Check if the circular linked list is empty.
        
        Returns:
            bool: True if empty, False otherwise
        """
        return self.head is None

    def length(self) -> int:
        """Get the number of nodes in the circular linked list.
        
        Returns:
            int: Number of nodes
        """
        return self._size

    def append(self, data) -> None:
        """Append a new node with the given data to the end of the circular linked list.
        
        Args:
            data: Data to be appended
        Raises:
            ValueError: If data is None
        """
        new_node = Node(data)
        self._size += 1
        if not self.head:
            self.head = new_node
            new_node.next = self.head
            return
        last = self.head
        while last.next != self.head:
            last = last.next
        last.next = new_node
        new_node.next = self.head

    def display(self) -> None:
        """Display the circular linked list."""
        if self.is_empty():
            print("None")
            return
        current = self.head
        while True:
            print(current.data, end=" -> ")
            current = current.next
            if current == self.head:
                break
        print(f"(head: {self.head.data})")

    def __str__(self) -> str:
        """Return string representation of the circular linked list.
        
        Returns:
            str: String representation
        """
        if self.is_empty():
            return "None"
        elements = []
        current = self.head
        while True:
            elements.append(str(current.data))
            current = current.next
            if current == self.head:
                break
        return " -> ".join(elements) + f" -> (head: {self.head.data})"

    def insert_at_beginning(self, data) -> None:
        """Insert a new node at the beginning of the circular linked list.
        
        Args:
            data: Data to be inserted
        Raises:
            ValueError: If data is None
        """
        new_node = Node(data)
        self._size += 1
        if not self.head:
            self.head = new_node
            new_node.next = self.head
            return
        last = self.head
        while last.next != self.head:
            last = last.next
        new_node.next = self.head
        self.head = new_node
        last.next = self.head

    def insert_at_end(self, data) -> None:
        """Insert a new node at the end of the circular linked list.
        
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
        new_node = Node(data)
        self._size += 1
        current = self.head
        for _ in range(position - 1):
            current = current.next
        new_node.next = current.next
        current.next = new_node

    def delete_at_beginning(self) -> None:
        """Delete the node at the beginning of the circular linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self._size -= 1
        if self.head.next == self.head:
            self.head = None
            return
        last = self.head
        while last.next != self.head:
            last = last.next
        self.head = self.head.next
        last.next = self.head

    def delete_at_end(self) -> None:
        """Delete the node at the end of the circular linked list.
        
        Raises:
            ValueError: If list is empty
        """
        if self.is_empty():
            raise ValueError("Cannot delete from empty list")
        self._size -= 1
        if self.head.next == self.head:
            self.head = None
            return
        current = self.head
        while current.next.next != self.head:
            current = current.next
        current.next = self.head

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
        self._size -= 1
        current = self.head
        for _ in range(position - 1):
            current = current.next
        current.next = current.next.next

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
        if self.is_empty():
            return -1
        current = self.head
        position = 0
        while True:
            if current.data == data:
                return position
            current = current.next
            position += 1
            if current == self.head:
                break
        return -1

    def reverse(self) -> None:
        """Reverse the circular singly linked list."""
        if self.is_empty() or self.head.next == self.head:
            return
        prev = None
        current = self.head
        next_node = None
        tail = self.head
        while True:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
            if current == self.head:
                break
        self.head = prev
        tail.next = self.head