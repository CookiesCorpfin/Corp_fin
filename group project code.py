import warnings
warnings.filterwarnings("ignore")
import wrds
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression




# For statistics. Requires statsmodels 5.0 or more
from statsmodels.formula.api import ols
# Analysis of Variance (ANOVA) on linear models
from statsmodels.stats.anova import anova_lm




#some practical stuff
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 10000)
#pd.set_option('display.max_colwidth', None)

#connect to wrds
conn = wrds.Connection(wrds_username = 'your_username')

# set variable list (#first three are discount brokerage firms, then 4 banks (we must insert from palne webber)then yahoo )
#WRONG > variable_list = ['80851310','74837610','94154710','28176010','07390210','55113710','61744610']

#variable_list = ['80851310','74837610','94154710']



def main(variable_list):
    

    #61744610 stopas at 1997/06/01

    #set time window 
    beg_date = '08/31/1992'
    end_date = '08/31/1997'
    if variable_list==['94154710']:
        end_date = '09/30/1996'
    #import data from ff lib
    starting_table = conn.raw_sql("""select dateff, mktrf, rf, smb, hml, rmw, cma, umd
                                    from ff_all.fivefactors_monthly 
                                    where 
                                    dateff>= '"""+beg_date+"""'
                                    AND  dateff <= '"""+end_date+"""'
                                    """, date_cols=['dateff'])

    #print(starting_table)
    #print("\n\n")
    print("Cusip: "+variable_list[0])

    #set empty column for mkt cap
    starting_table["Total Value of the Market"]= 0 * starting_table["rf"]

    starting_table["pf_ret"]= 0 * starting_table["rf"]

    #set ones column
    """pd.to_numeric(numpy.ones(len(starting_table["rf"])))"""

    #import data for analysis and create df
    for variable in variable_list:
        
        variable_table = conn.raw_sql("""select cusip, prc, ret, shrout, date
                                        from crsp_a_stock.msf
                                        where cusip='"""+variable+"""'
                                        and date>= '"""+beg_date+"""'
                                        AND  date <= '"""+end_date+"""'
                                        """, date_cols=['date'])
        
        starting_table["price", variable] = variable_table['prc']
        starting_table["ret", variable] = variable_table['ret']

        #
        #fill Nan
        variable_table.fillna(value=0, inplace = True)
        
        
        #find mkt cap
        variable_table["market Cap",variable] = variable_table["prc"]*variable_table["shrout"]
        #
        #print(variable_table)
        #print("\n\n\n\n\n")
        variable_table.drop(columns =['date'], inplace = True)
        
        
        #find total value of the mkt
        starting_table["Total Value of the Market"] = starting_table["Total Value of the Market"].add(variable_table["market Cap",variable],fill_value=0)
        #print(starting_table["Total Value of the Market"] + variable_table["market Cap",variable])
        
        #concatenate
        starting_table = pd.concat([starting_table, variable_table], axis=1)

        
    df1 = starting_table.pop('Total Value of the Market')
    starting_table["Total Value of the Market"] = df1


    #compute mkt share
    for variable in variable_list:
        #starting_table["market share", variable] = starting_table["market Cap",variable] / starting_table["Total Value of the Market"]
        starting_table["market share", variable] = starting_table["market Cap",variable].div(starting_table["Total Value of the Market"],fill_value=0)

    #compute weighted pf return
    for variable in variable_list:
        #starting_table["pf_ret"] = (starting_table["market share",variable] * starting_table["ret", variable]) + starting_table["pf_ret"]
        starting_table["pf_ret"] = (starting_table["market share",variable].mul(starting_table["ret", variable],fill_value=0)) + starting_table["pf_ret"]

    #polish
    starting_table.drop(columns =['cusip','ret','prc'], inplace = True)
    #fra added
    for variable in variable_list:
            starting_table.drop(columns =[("price",variable),("market Cap",variable)], inplace = True)
    starting_table.drop(columns =['shrout'], inplace = True)

    # drop last n rows
    starting_table.drop(starting_table.tail(0).index,inplace=True) 

    #fill Nan
    #starting_table.fillna(value=0, inplace = True)

    #print(starting_table)
    #print("\n\n\n")
    #print(starting_table.to_csv())

##    # linear regression model
##    x = np.array(starting_table[["mktrf","smb","hml"]]).reshape((-1, 1))
##    y = np.array(starting_table["pf_ret"]).reshape((-1, 1))
##
##    #print(x)
##    #print(y)
##
##    reg = LinearRegression().fit(x, y)
##
##    print("R^2", reg.score(x, y))
##
##    print("Beta1", reg.coef_)
##
##    print("Intercept", reg.intercept_)
##
##    #print(reg.get_params)



    # Fit the model
    #model = ols("pf_ret ~ mktrf", starting_table).fit()
    model = ols("pf_ret ~ mktrf + smb + hml + rmw + cma + umd", starting_table).fit()

    # Print the summary
    #print(model.summary())

    print("\nRetrieving manually the parameter estimates:")
    print(np.array2string(model._results.rsquared,prefix="")+"\n"+((np.array2string(model._results.params[1:],separator="\n",prefix="")).replace(" ","").replace("[","").replace("]",""))+"\n"+((np.array2string(model._results.params[0],separator="\n",prefix="")).replace(" ","").replace("[","").replace("]","")))
    print("\n\n")
    # Peform analysis of variance on fitted linear model
    #anova_results = anova_lm(model)

    #print('\nANOVA results')
    #print(anova_results)




#variable_list = ['80851310','74837610','94154710']
variable_list = ['28176010','07390210','59018810','61744644']


#Charles Schwab - 80851310
#Quick & Reilly - 74837610
#Waterhouse - 94154710

#Edwards A G - 28176010
#Bear Sterns - 07390210
#Merrill Lynch - 59018810
#Morgan Stanley Dean Witter - 61744644

#Microsoft - 59491810
#IBM - 45920010
#Intel - 45814010

print("Split Portfolio 1:")
main(['80851310'])
main(['74837610'])
main(['94154710'])

print("Split Portfolio 2:")
main(['28176010'])
main(['07390210'])
main(['59018810'])
main(['61744644'])

print("Split Portfolio 3:")
main(['59491810'])
main(['45920010'])
main(['45814010'])

print("Portfolio 1:")
main(['80851310','74837610','94154710'])
print("Portfolio 2:")
main(['28176010','07390210','59018810','61744644'])
print("Portfolio 3:")
main(['59491810','45920010','45814010'])



beg_date = '01/01/1950'
end_date = '08/31/1997'
ff_table = conn.raw_sql("""select dateff, mktrf, rf, smb, hml, rmw, cma, umd
                                    from ff_all.fivefactors_monthly 
                                    where 
                                    dateff>= '"""+beg_date+"""'
                                    AND  dateff <= '"""+end_date+"""'
                                    """, date_cols=['dateff'])

#"pf_ret ~ mktrf + smb + hml + rmw + cma + umd"
#print(ff_table)
#print(ff_table.mean())
print()
print(((1+ff_table.mean())**12)-1)

