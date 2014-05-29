#------------------------------------------------------------------
# R defaults to mersenne twister
#------------------------------------------------------------------
set.seed(1)
RNGkind()

#------------------------------------------------------------------
# Dump the full state of the mersenne twister
# Convert R's int32 representation to the actual uint32 representation
#------------------------------------------------------------------
tseed <- .Random.seed[3:626]
length(tseed)
# convert signed to unsigned 32 bit int
tseed[tseed < 0] <- tseed[tseed < 0] + 2^32
sink("R_seed_and_randoms.py")
	cat("seed = [")
	cat(paste(tseed, collapse=', '))
	cat("]\n")


#------------------------------------------------------------------
# Dump the first 1000 uniform random numbers
#------------------------------------------------------------------
	cat("randoms = [")
	cat(paste(runif(1000), collapse=', '))
	cat("]\n")
sink()