import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
sorted_columns = ['OLF','Isocortex','HPF','CTXsp','CNU','TH','HY','MB','CB','P','MY','Other']
group1 = ['OLF','Isocortex','HPF','CTXsp','CNU','TH','HY']
group2 = ['P','MY','Other']
group3= ['MB','CB']

def plot_correlation(df):
    '''
    Plot the correlation of projection percentages to each brain region
    '''
    df = df[sorted_columns]
    corr = df.corr(method='spearman')
    plt.figure()
    sns.heatmap(corr,square=True, linewidth=.5, vmin=-1, center=0, cmap='icefire')
    plt.title('Original data')

def plot_shuffle(df):
    '''
    Shuffle each cell's projections, then plot the correlation matrix
    '''
    x_shuffle = np.apply_along_axis(np.random.permutation,1,df.to_numpy())
    df_shuffle = pd.DataFrame(x_shuffle, columns=sorted_columns)
    corr_shuffle = df_shuffle.corr(method='spearman')
    plt.figure()
    sns.heatmap(corr_shuffle,square=True, linewidth=.5, vmin=-1, center=0, cmap='icefire')
    plt.title('Shuffle each cell\'s projections')

def plot_random(df):
    # Plot correlation in randomly generated projection patterns
    df_random = df.copy()
    for i in range(len(df_random)):
        x = np.random.rand(len(sorted_columns))
        df_random.iloc[i,:] = x/np.sum(x)
    corr_random = df_random.corr(method='spearman')
    plt.figure()
    sns.heatmap(corr_random, square=True, linewidth=.5, vmin=-1, center=0, cmap='icefire')
    plt.title('Random projections')

def shuffle_all(df):
    x_shuffle = np.apply_along_axis(np.random.permutation,1,df.to_numpy())
    df_shuffle = pd.DataFrame(x_shuffle, columns=sorted_columns)
    corr_shuffle = df_shuffle.corr(method='spearman')
    return np.linalg.norm(corr_shuffle)

def test_all(df,n=10000):
    corr = df.corr(method='spearman')
    orig_norm = np.linalg.norm(corr)
    norms = [shuffle_all(df) for x in range(n)]
    p = np.mean(np.array(norms) > orig_norm)
    print('Probability of observing data in shuffle distribution: {}'.format(p))
    plot_hist(norms, orig_norm)
   
def plot_hist(norms, data_norm):
    plt.figure(figsize=(3,2))
    plt.xlabel('Norm of Correlation matrix')
    plt.ylabel('count')
    plt.axvline(data_norm,color='r',label='data')
    plt.hist(norms,bins=30,label='Shuffle cells')

def shuffle_group(df,test_group):
    '''
        Shuffle each cell's projections within the subset of regions 
        defined in test_group. Then compute the norm of the correlation matrix
    '''
    x_shuffle = np.apply_along_axis(np.random.permutation,1,df[test_group].to_numpy())
    df_group = pd.DataFrame(x_shuffle,columns=test_group)
    corr_group = df_group.corr(method='spearman')
    return np.linalg.norm(corr_group)

def test_group(df,test_group,n=10000):
    corr = df.corr(method='spearman')
    orig_norm = np.linalg.norm(corr.loc[test_group,test_group])
    norms = [shuffle_group(df,test_group) for x in range(n)]
    plot_hist(norms, orig_norm)
    p = np.mean(np.array(norms) > orig_norm)
    print('Probability of observing data in shuffle distribution: {}'.format(p))

def shuffle_lengths(df_unnormalized):  
    temp = df_unnormalized.copy()
    for col in temp.columns.values:
        temp[col] = temp[col].sample(frac=1).values
    temp = temp.divide(temp.sum(axis=1),axis=0)
    corr = temp.corr(method='spearman')
    plt.figure()
    sns.heatmap(corr,square=True, linewidth=.5, vmin=-1, center=0, cmap='icefire')
    plt.title('shuffle columns')

