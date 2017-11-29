import numpy as np

class Env:
    def __init__(self,boardsize=9,komi=6.5):

        self.boardsize = boardsize

        self.komi = komi

        self.reset()

    def reset(self):

        self.board = np.zeros((self.boardsize,self.boardsize),dtype=np.int8)

        self.history = []

        self.update_legals()

    def get_neighbors(self,vertex):
        
        _x,_y = vertex

        _list = []

        def inside(x,y):
            if x >= 0 and x < self.boardsize and y >= 0 and y < self.boardsize:
                return True
            else:
                return False

        for i in range(-1,2):
            if i==0:
                continue
            if inside(_x+i,_y):
                _list.append((_x+i,_y))
            if inside(_x,_y+i):
                _list.append((_x,_y+i))
        return _list

    def get_connected(self,board,vertex,traversed=None):
        nbh = self.get_neighbors(vertex)
        
        if traversed == None:
            traversed = [vertex]
        else:
            traversed.append(vertex)
#        print vertex, nbh, traversed
 #       raw_input()

        for p in nbh:
            if p in traversed:
                continue
  #          print p, board[p], vertex, board[vertex]
            if board[p] == board[vertex]:
                self.get_connected(board,p,traversed)

        return traversed


    def check_alive(self,board,vertex):
        """
        Return True if empty or alive, else return False
        """
        if board[vertex] == 0:
            return True

        connected = self.get_connected(board,vertex)

        for p in connected:

            nbh = self.get_neighbors(p)

            for _nbh in nbh:

                if board[_nbh] == 0:
                    return True

        return False

    def check_suicide(self,board,vertex):
        """
        Return True if suicide, else return False
        """
        if self.check_alive(board,vertex):
            return False
        else:
            return True

    def capture_neighbors(self,vertex):

        nbh = self.get_neighbors(vertex)

        for p in nbh:
            if self.board[p] == 0:
                continue
            if (self.board[p] != self.board[vertex] and
                    not self.check_alive(self.board,p)):
                _c = self.get_connected(self.board,p)
                for p2 in _c:
                    self.board[p2] = 0

    def play(self,color,vertex):

        if vertex not in self.legals[color]:
            return False

        
        self.history.append(self.board)

        self.board = np.copy(self.board)
        if color == 'black':
            self.board[vertex] = 1
        else:
            self.board[vertex] = -1

        self.capture_neighbors(vertex)

        self.update_legals()

        return True

    def check_superko(self,board):
        """
        Return True if violation, else return False
        """
        for b in self.history:
            if np.array_equal(b,board):
                return True
        return False

    def update_legals(self):

        list_b, list_w = self.list_of_legals()

        self.legals = {'black':list_b, 'white':list_w}

    def list_of_legals(self):

        list_of_empty = zip(*np.where(self.board==0))

        _list_w = []
        _list_b = []

        for p in list_of_empty:
            
            tmp_board_b = np.copy(self.board)
            tmp_board_b[p] = 1
            tmp_board_w = np.copy(self.board)
            tmp_board_w[p] = -1

            if not (self.check_superko(tmp_board_b) or self.check_suicide(tmp_board_b,p)):
                _list_b.append(p)

            if not (self.check_superko(tmp_board_w) or self.check_suicide(tmp_board_w,p)):
                _list_w.append(p)

        return _list_b,_list_w


