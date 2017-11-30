import numpy as np

class Env:
    def __init__(self,boardsize=9,komi=6.5):

        self.boardsize = boardsize

        self.komi = komi

        self.reset()

    def reset(self):

        self.board = np.zeros((self.boardsize,self.boardsize),dtype=np.int16)
        
        self.liberty = np.zeros((self.boardsize,self.boardsize),dtype=np.int16) 

        self.history = []

        self.update_liberty()

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
            traversed = set([vertex])
        else:
            traversed.add(vertex)
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

    def capture_neighbors(self,board,vertex):

        nbh = self.get_neighbors(vertex)

        for p in nbh:
            if board[p] == 0:
                continue
            if (board[p] != board[vertex] and
                    self.liberty[p] == 1):
                _c = self.get_connected(board,p)
                for p2 in _c:
                    board[p2] = 0

    def play(self,color,vertex):

        if vertex not in self.legals[color]:
            return False

        
        self.history.append(self.board)

        self.board = self.legals[color][vertex] 
#        self.board = np.copy(self.board)
 #       if color == 'black':
  #          self.board[vertex] = 1
   #     else:
    #        self.board[vertex] = -1

       # self.capture_neighbors(self.board,vertex)

        self.update_liberty()

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

        list_b = self.list_of_legals('black')
        list_w = self.list_of_legals('white')

        self.legals = {'black':list_b, 'white':list_w}

    def list_of_legals(self,color):

        list_of_empty = zip(*np.where(self.board==0))

        _list = {'pass':np.copy(self.board)}

        if color == 'black':
            v = 1
        else:
            v = -1

        for p in list_of_empty:
            
            if self.liberty[p] > 0:
                _is_suicide = False
            else:
                _is_suicide = True
                for _n in self.get_neighbors(p):
                    if self.board[_n] == v and self.liberty[_n] > 1:
                        _is_suicide = False
                    elif self.board[_n] == -v and self.liberty[_n] == 1:
                        _is_suicide = False
            if _is_suicide:
                continue

            tmp_board = np.copy(self.board)
            tmp_board[p] = v
            self.capture_neighbors(tmp_board,p)
            
            if not (self.check_superko(tmp_board)):
                _list[p] = tmp_board


        return _list

    def update_liberty(self):

        traversed = set([]) 

        for i in range(self.boardsize):
            for j in range(self.boardsize):

                v = (i,j)
                

                if v in traversed:
                    continue

                traversed.add(v)
                if self.board[v] == 0:
                    _count = 0
                    for p in self.get_neighbors(v):
                        if self.board[p] == 0:
                            _count += 1
                    self.liberty[v] = _count
                    continue

                _c = self.get_connected(self.board,v)

                traversed |= _c

                liberty_set = set([])

                for p in _c:

                    nbh = self.get_neighbors(p)
                    
                    for p2 in nbh:

                        if self.board[p2] == 0:

                            liberty_set.add(p2)

                liberties = len(liberty_set)

                for p in _c:

                    self.liberty[p] = liberties

    def score(self):
        traversed = []
        
        b_score = 0
        w_score = 0

        for i in range(self.boardsize):
            for j in range(self.boardsize):
                v = (i,j)
                if v in traversed:
                    continue
                _c = self.get_connected(self.board,v)
                traversed += _c
                
                if self.board[v] == 1:
                    b_score += len(_c)
                elif self.board[v]:
                    w_score += len(_c)
                else:
                    reach_b = False
                    reach_w = False
                    for p in _c:
                        nbh = self.get_neighbors(p)
                        for p2 in nbh:
                            if self.board[p2] == 1:
                                reach_b = True
                            if self.board[p2] == -1:
                                reach_w = True
                            if reach_b and reach_w:
                                break
                        if reach_b and reach_w:
                            break
                    if reach_b and not reach_w:
                        b_score += len(_c)
                    if not reach_b and reach_w:
                        w_score += len(_c)
        return b_score-w_score-self.komi
