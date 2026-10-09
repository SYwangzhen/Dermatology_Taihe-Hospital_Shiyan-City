## debug check (ASCII only) -- force REAL mode
source("00_config.R")
DEMO_MODE <- FALSE
source("01_load_clean.R")
d <- load_data()
a <- d$asr
cat("measures in asr:", unique(a$measure), "\n")
inc <- a[a$location == "China" & a$sex == "Both" & a$measure == "Incidence", ]
cat("inc rows:", nrow(inc), " val[1:3]:", head(inc$val, 3), "\n")
dal <- a[a$location == "China" & a$sex == "Both" & a$measure == "DALYs (Disability-Adjusted Life Years)", ]
cat("dal(full-name) rows:", nrow(dal), "\n")
agesex <- d$agesex
cat("agesex ages:", sort(unique(agesex$age)), "\n")
