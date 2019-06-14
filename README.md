# ChainDrug_BlockChain_Implementation
This is a block chain application which can be used to curb drug trafficking

**Team Members**:
>>	Parameswar K\
>>	Bhanu Vikas Yaganti\
>>	Sai Surya U\
>>	Pavan Ganesh V\
>>	Aman Mohammad

**Project Description**:\
	A conceptual blockchain track drug sales.\
	The idea is to have a way to ensure that at every trasaction is tracked and accounted.



1. Run this ChainDrug.py with 4 nodes by doing the following commands:\
	
>	python3 ChainDrug.py -p 5000\
>	python3 ChainDrug.py -p 5001\
>	python3 ChainDrug.py -p 5002\
>	python3 ChainDrug.py -p 5003


2. Create a transaction at a particular client by sending a post request to the following URL
	
	http://localhost:5000/transactions/new

	by passing the following data\
	{
	+	"owner" : 5001,
	+	"receiver" : 5002,
	+	"amount" : 400,
	+	"drug_id" : 52856,
	+	"x" : 25
	}


3. Mine a block of transcations at a node by
	
	http://localhost:5000/mine


4. To view the chain at a node
	
	http://localhost:5001/chain


5. To view transactions of a particular user
	
	http://localhost:5000/viewUser/<user_port>
