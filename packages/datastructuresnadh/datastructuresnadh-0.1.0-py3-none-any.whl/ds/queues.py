""" Queues implementation """
class SimpleQueue:
  ## Generate a Doc string for the class. Provide a brief description of the class and its purpose.
  
  """
  A simple Queue implementation using a list. 
  The queue has a maximum size and supports basic operations such as enqueue, dequeue, and peek.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  The queue supports a maximum size, and if the queue is full, an overflow message is displayed.
  If the queue is empty, an underflow message is displayed when trying to dequeue or peek.
  The queue supports basic operations such as enqueue, dequeue, and peek.
  The queue can be printed to show the elements in the queue.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  
  """
  
  def __init__(self,max:int=10) -> None:
    self.Q: list =[None] * max
    self.max_size: int =max
    self.front :int=-1
    self.rear:int=-1
    
  def Enqueue(self,v:int) -> None:
    if self.rear==self.max_size-1:
      print("Queue Overflow")
      return
    if self.front==-1 and self.rear==-1:
      self.front+=1
      self.rear+=1
      self.Q[int(self.rear)]=v
      print(f"element Inserted Succesfully. Rear: {self.rear}")
    else:
      self.rear+=1
      self.Q[self.rear]=v
      print(f"element Inserted Succesfully. Rear: {self.rear}")
      
  def Dequeue(self) -> int:
    if self.front==-1:
      print("Underflow")
      return
    val:int=self.Q[self.front]
    if self.front==self.rear:
      self.front=self.rear=-1
      return val
    else:
      self.front+=1
      return val
    
  def peek(self)-> int:
    return self.Q[self.front]
  
  
  def printQ(self) -> None:
    if self.front==-1:
      print("Underflow")
      return
    else:
      for i in range(self.front,self.rear+1):
        print(f"The Element in {i}: {self.Q[i]}")
        
  @property
  def front(self)-> int:
    return self.front
  
  @property
  def size(self)-> int:
    if self.front==-1:
      return 0
    else:
      return self.rear-self.front+1
  
  @property
  def isEmpty(self)-> bool:
    if self.front==-1:
      return True
    else:
      return False
  
      
    
      


class CircularQueue:
  """
  A Circular Queue implementation using a list. 
  The queue has a maximum size and supports basic operations such as enqueue, dequeue, and peek.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  The queue supports a maximum size, and if the queue is full, an overflow message is displayed.
  If the queue is empty, an underflow message is displayed when trying to dequeue or peek.
  The queue supports basic operations such as enqueue, dequeue, and peek.
  The queue can be printed to show the elements in the queue.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  
  """
  
  def __init__(self,max:int=10) -> None:
    self.Q: list =[None] * max
    self.max_size: int =max
    self.front :int=-1
    self.rear:int=-1
  
  def Enqueue(self,v:int) -> None:
    if (self.rear+1)%self.max_size==self.front:
      print("Queue Overflow")
      return
    if self.front==-1 and self.rear==-1:
      self.front+=1
      self.rear+=1
      self.Q[int(self.rear)]=v
      print(f"element Inserted Succesfully. Rear: {self.rear}")
    else:
      self.rear=(self.rear+1)%self.max_size
      self.Q[self.rear]=v
      print(f"element Inserted Succesfully. Rear: {self.rear}")
  
  def Dequeue(self) -> int:
    if self.front==-1:
      print("Underflow")
      return
    val:int=self.Q[self.front]
    if self.front==self.rear:
      self.front=self.rear=-1
      return val
    else:
      self.front=(self.front+1)%self.max_size
      return val
  
  def peek(self)-> int:
    return self.Q[self.front]   
  
  def printQ(self) -> None: 
    if self.front==-1:
      print("Underflow")
      return
    else:
      i:int=self.front
      while True:
        print(f"The Element in {i}: {self.Q[i]}")
        if i==self.rear:
          break
        i=(i+1)%self.max_size
  
  
class PriorityQueue:
  """
  A Priority Queue implementation using a list. 
  The queue has a maximum size and supports basic operations such as enqueue, dequeue, and peek.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  The queue supports a maximum size, and if the queue is full, an overflow message is displayed.
  If the queue is empty, an underflow message is displayed when trying to dequeue or peek.
  The queue supports basic operations such as enqueue, dequeue, and peek.
  The queue can be printed to show the elements in the queue.
  The queue is implemented using a list, and the front and rear pointers are used to keep track of the elements in the queue.
  
  """
  
  def __init__(self,max:int=10) -> None:
    self.Q: list =[None] * max
    self.max_size: int =max
    self.front :int=-1
    self.rear:int=-1
  def Enqueue(self,v:int) -> None:
    if self.rear==self.max_size-1:
      print("Queue Overflow")
      return
    if self.front==-1 and self.rear==-1:
      self.front+=1
      self.rear+=1
      self.Q[int(self.rear)]=v
      print(f"element Inserted Succesfully. Rear: {self.rear}")
    else:
      i:int=self.rear-1
      while i>=0 and v>self.Q[i]:
        self.Q[i+1]=self.Q[i]
        i-=1
      self.Q[i+1]=v
      self.rear+=1
      print(f"element Inserted Succesfully. Rear: {self.rear}")
  def Dequeue(self) -> int:
    if self.front==-1:
      print("Underflow")
      return
    val:int=self.Q[self.front]
    if self.front==self.rear:
      self.front=self.rear=-1
      return val
    else:
      self.front+=1
      return val
  def peek(self)-> int:
    return self.Q[self.front]
  def printQ(self) -> None:
    if self.front==-1:
      print("Underflow")
      return
    else:
      for i in range(self.front,self.rear+1):
        print(f"The Element in {i}: {self.Q[i]}")
  def isEmpty(self)-> bool:
    if self.front==-1:
      return True
    else:
      return False
  def isFull(self)-> bool:
    if self.rear==self.max_size-1:
      return True
    else:
      return False
  @property
  def front(self)-> int:
    return self.front
  @property
  def size(self)-> int:
    if self.front==-1:
      return 0
    else:
      return self.rear-self.front+1
    
  
     
      
      
      

  