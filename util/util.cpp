#include<vector>
#include<set>
#include<iostream>

static std::vector< std::vector<int> > nbh_map;

inline int to_index(int *x,int size){
	return x[0]*size+x[1];
}
extern "C"{
	void copy(int *arr,int *arr2,int size){
		for(int i=0;i<size;++i){
			arr[i]=arr2[i];
		}
	}
	void init_neighbors(int size){
		for(int i=0;i<size;++i){
			for(int j=0;j<size;++j){
				std::vector<int> tmp;
				if(i+1<size)
					tmp.push_back((i+1)*size+j);
				if(i-1>=0)
					tmp.push_back((i-1)*size+j);
				if(j+1<size)
					tmp.push_back(i*size+(j+1));
				if(j-1>=0)
					tmp.push_back(i*size+(j-1));
				nbh_map.push_back(tmp);
			}
		}
	}
	std::vector<int> get_neighbors(int size,int idx){
		return nbh_map[idx];
	}
	/*
	std::vector<int> get_neighbors(int size,int idx){

		int x[2] = {idx/size,idx%size};

		std::vector<int> result;

		if(x[0]+1<size){
			int tmp[2] = {x[0]+1,x[1]};
			result.push_back(to_index(tmp,size));
		}
		if(x[0]-1>=0){
			int tmp[2] = {x[0]-1,x[1]};
			result.push_back(to_index(tmp,size));
		}
		if(x[1]+1<size){
			int tmp[2] = {x[0],x[1]+1};
			result.push_back(to_index(tmp,size));
		}
		if(x[1]-1>=0){
			int tmp[2] = {x[0],x[1]-1};
			result.push_back(to_index(tmp,size));
		}
		return result;
	}
	*/
	std::set<int> get_connected(int *board,int size,int idx){
		std::vector<int> nbh = get_neighbors(size,idx);
		
		std::vector<int> to_traverse(nbh.begin(),nbh.end());

		std::set<int> result;
		result.insert(idx);

		for(int i = 0;i < to_traverse.size();++i){
			int _idx = to_traverse[i];
			if(result.find(_idx)!=result.end())
				continue;
			if(board[_idx]==board[idx]){
				result.insert(_idx);
				nbh = get_neighbors(size,_idx);
				to_traverse.insert(to_traverse.end(),nbh.begin(),nbh.end());
			}

		}
		return result;
	}

	void count_liberty(int *board,int *liberty,int size){

		std::set<int> traversed;

		for(int i=0;i<size*size;++i){

			if(traversed.find(i)!=traversed.end())
				continue;

			liberty[i] = 0;


			if(board[i]==0){

				std::vector<int> nbh = get_neighbors(size,i);

				for(auto it = nbh.begin();it!=nbh.end();++it)
					if(board[*it]==0)
						liberty[i] += 1;	
				
			}else{

				auto _c = get_connected(board,size,i);
				
				std::set<int> empty_set;

				for(auto _c_it = _c.begin();_c_it!=_c.end();++_c_it){
					traversed.insert(*_c_it);
					std::vector<int> nbh = get_neighbors(size,*_c_it);
					for(auto nbh_it = nbh.begin();nbh_it!=nbh.end();++nbh_it)
						if(board[*nbh_it]==0)
							empty_set.insert(*nbh_it);
					
				}
				int _lib = empty_set.size();
				for(auto _c_it = _c.begin();_c_it!=_c.end();++_c_it)
					liberty[*_c_it] = _lib;
				
			}

		}	
	}

	void capture_neighbors(int *board,int *liberty,const int size,const int idx){

		std::vector<int> nbh = get_neighbors(size,idx);
		

		for(auto it = nbh.begin();it!=nbh.end();++it){
		
			if(board[*it]==0)
				continue;

			if( (liberty[*it] == 1) && (board[*it] == -board[idx]) ){
				std::set<int> _c = get_connected(board,size,*it);
				for(auto _it=_c.begin();_it!=_c.end();++_it)
					board[*_it] = 0;
				
			}
		}
	}

	bool is_suicide(int *board, int *liberty, int size, int val, int idx){
		

		if(liberty[idx]>0){

			return false;

		}else{

		    bool suicide = true;

			std::vector<int> nbh = get_neighbors(size,idx);

			for(auto it = nbh.begin();it!=nbh.end();++it){
				if( board[*it] == val && liberty[*it] > 1 )
					return false;
				else if( board[*it] == -val && liberty[*it] == 1 )
					return false;
			}	
		}
		
		return true;
	}
}
