import numpy as np

class Env:
    def __init__(self,boardsize=9,komi=6.5):

        self.boardsize = boardsize

        self.komi = komi

        self.reset()

    def reset(self):

        self.init_neighbors()

        self.board = np.zeros((self.boardsize,self.boardsize),dtype=np.int8)
        
        self.liberty = np.zeros((self.boardsize,self.boardsize),dtype=np.int32) 
        self.init_liberty()


        self.history = []

        self.update_legals()

    def init_neighbors(self):
        """
        Construct neighbors' dict w.r.t boardsize
        """
        self.neighbors = {}

        def inside(x,y):
            if x >= 0 and x < self.boardsize and y >= 0 and y < self.boardsize:
                return True
            else:
                return False

        for i in xrange(self.boardsize):
            for j in xrange(self.boardsize):
                _list = []
                for k in xrange(-1,2):
                    if k == 0:
                        continue
                    if inside(i+k,j):
                        _list.append((i+k,j))
                    if inside(i,j+k):
                        _list.append((i,j+k))
                self.neighbors[(i,j)] = _list
        

    def get_neighbors(self,vertex):
        """
        Return list of neighbors of vertex
        """
        return self.neighbors[vertex]

    def get_connected(self,board,vertex,traversed=None):
        """
        Return a set with vertices connected to vertex
        """
        nbh = self.get_neighbors(vertex)

        if traversed == None:
            traversed = set([vertex])
        else:
            traversed.add(vertex)

        for p in nbh:
            if p in traversed:
                continue
            if board[p] == board[vertex]:
                self.get_connected(board,p,traversed)

        return traversed

    def get_connected_iter(self,board,vertex):
        """
        Return a set of vertices that are connected to vertex (iterative)
        """
        nbh = self.neighbors[vertex]

        traversed = set([vertex])

        v_left = list(nbh)

        for _v in v_left:
            
            if _v in traversed:
                continue

            if board[_v] == board[vertex]:
                traversed.add(_v)
                v_left += self.get_neighbors(_v)

        return traversed


    def check_alive(self,board,vertex):
        """
        Return True if empty or alive, else return False
        """
        if board[vertex] == 0:
            return True

        connected = self.get_connected_iter(board,vertex)

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
        """
        Scan neighbors with liberty = 1 and capture them
        """
        nbh = self.get_neighbors(vertex)

        for p in nbh:
            if board[p] == 0:
                continue
            if (board[p] != board[vertex] and
                    self.liberty[p] == 1):
                _c = self.get_connected_iter(board,p)
                for p2 in _c:
                    board[p2] = 0

    def play(self,color,vertex):

        if vertex not in self.legals[color]:
            return False

        
        self.history.append(self.board)

        self.board = self.legals[color][vertex] 

        self.update_liberty()

        self.update_legals()

        return True

    def check_superko(self,board):
        """
        Return True if violation, else return False
        """
        def board_equal(b1,b2):
            for i in xrange(self.boardsize):
                for j in xrange(self.boardsize):
                    if b1[i][j] != b2[i][j]:
                        return False
            return True
        
        _MAX_KO_LENGTH = 15

        length = min(_MAX_KO_LENGTH,len(self.history))

        for i in xrange(length):
            if board_equal(board,self.history[-1-i]):
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

    def init_liberty(self):
        for i in range(self.boardsize):
            for j in range(self.boardsize):
                v = (i,j)
                self.liberty[v] = len(self.get_neighbors(v))

    def count_liberty(self,board,vertex_set):

        liberty_set = set([])

        for v in vertex_set:
            for n in self.get_neighbors(v):
                if board[n] == 0:
                    liberty_set.add(n)

        return len(liberty_set)


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

                _c = self.get_connected_iter(self.board,v)

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
                _c = self.get_connected_iter(self.board,v)
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
                            elif self.board[p2] == -1:
                                reach_w = True
                            if reach_b and reach_w:
                                break
                        if reach_b and reach_w:
                            break
                    if reach_b and not reach_w:
                        b_score += len(_c)
                    elif not reach_b and reach_w:
                        w_score += len(_c)
        return b_score-w_score-self.komi
