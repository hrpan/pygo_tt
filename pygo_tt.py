import numpy as np
from numpy.ctypeslib import ndpointer
from ctypes import *
from os.path import dirname
util_lib = CDLL(dirname(__file__)+'/util/util.so')

ndintptr = ndpointer(c_int,flags='C')
intptr = POINTER(c_int)
c_init_neighbors = util_lib.init_neighbors
c_init_neighbors.argtypes = [c_int]
c_init_neighbors.restype = None

c_count_liberty = util_lib.count_liberty
c_count_liberty.argtypes = [intptr,intptr,c_int]
c_count_liberty.restype = None

c_list_of_legals = util_lib.list_of_legals
c_list_of_legals.argtypes = [intptr,intptr,intptr,intptr,intptr,c_int,c_int,c_int]
c_list_of_legals.restype = c_int

_MAX_KO_LENGTH = 15

class Env:
    def __init__(self,boardsize=9,komi=6.5):

        self.boardsize = boardsize

        self.komi = komi

        c_init_neighbors(boardsize)

        self.reset()

    def reset(self):

        self.init_neighbors()

        self.board = np.zeros((self.boardsize,self.boardsize),dtype=np.int32)
        
        self.liberty = np.zeros((self.boardsize,self.boardsize),dtype=np.int32) 
        self.init_liberty()

        self.legal_boards = {}

        self.history = []

        self.history_hash = set([])

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

        for i in range(self.boardsize):
            for j in range(self.boardsize):
                _list = []
                for k in range(-1,2):
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

        if vertex == 'pass':
            return True

        try:
            index = self.legals[color].index(vertex)
        except ValueError:
            return False
       
        self.history.append(self.board)

        #self.history_hash.add(tuple(self.board.flatten()))

        #self.board = self.legals[color][vertex] 
        self.board = self.legal_boards[color][index]
        #self.update_liberty()
        self.c_update_liberty()

        self.update_legals()

        return True

    def check_superko(self,board):
        """
        DEPRECATED
        Return True if violation, else return False
        """
        def board_equal(b1,b2):
            for i in range(self.boardsize):
                for j in range(self.boardsize):
                    if b1[i][j] != b2[i][j]:
                        return False
            return True

        length = min(_MAX_KO_LENGTH,len(self.history))

        for i in range(length):
            if board_equal(board,self.history[-1-i]):
                return True
        return False

    def check_superko_hash(self,board):
        """
        DPRECATED
        Test if board hash in history
        Return True if violation, else return False 
        """

        length = min(_MAX_KO_LENGTH,len(self.history_hash))

        _tuple = tuple(board.ravel())

        if _tuple in self.history_hash:
            return True
        else:
            return False

    def update_legals(self):
        
        list_b = self.c_list_of_legals('black')
        list_w = self.c_list_of_legals('white')

        #list_b = self.list_of_legals('black')
        #list_w = self.list_of_legals('white')


        self.legals = {'black':list_b, 'white':list_w}
    def is_suicide(self,v,p):
        """
        DEPRECATED
        """
        if self.liberty[p] > 0:
            return False
        else:
            for _n in self.get_neighbors(p):
                if self.board[_n] == v and self.liberty[_n] > 1:
                    return False
                elif self.board[_n] == -v and self.liberty[_n] == 1:
                    return False
        return True
   
    def list_of_legals(self,color):
        """
        DEPRECATED
        """
        list_of_empty = zip(*np.where(self.board==0))

        _list = {'pass':np.copy(self.board)}

        if color == 'black':
            v = 1
        else:
            v = -1

        for p in list_of_empty:

            _is_suicide = self.is_suicide(v,p)
            
            if _is_suicide:
                continue

            tmp_board = np.copy(self.board)
            tmp_board[p] = v
            self.capture_neighbors(tmp_board,p)

#            if not (self.check_superko(tmp_board)):
            if not (self.check_superko_hash(tmp_board)):
                _list[p] = tmp_board


        return _list
    def c_list_of_legals(self,color):

        if color == 'black':
            v = 1
        else:
            v = -1

        b_size = self.boardsize 

        result = np.zeros((b_size**2,b_size,b_size),dtype=np.int32)
        vertex = np.zeros(b_size**2,dtype=np.int32)
        history = np.array(self.history[-_MAX_KO_LENGTH:])

        board_ptr = self.board.ctypes.data_as(intptr)
        liberty_ptr = self.liberty.ctypes.data_as(intptr)
        result_ptr = result.ctypes.data_as(intptr)
        vertex_ptr = vertex.ctypes.data_as(intptr)
        history_ptr = history.ctypes.data_as(intptr)

        n_legals = c_list_of_legals(board_ptr,
                liberty_ptr,
                result_ptr,
                vertex_ptr,
                history_ptr,
                len(history),
                b_size,v)

        indices = np.unravel_index(vertex[:n_legals],(b_size,b_size))
        
        _list = list(zip(*indices))
        _list.append('pass')

        self.legal_boards[color] = result[:n_legals]
        
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
        #print(self.liberty)
    def c_update_liberty(self):


        size = self.boardsize
        b_ptr = self.board.ctypes.data_as(intptr)
        l_ptr = self.liberty.ctypes.data_as(intptr)
        c_count_liberty(b_ptr,l_ptr,size)

        #print(self.liberty)
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
