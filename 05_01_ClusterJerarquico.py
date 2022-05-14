# -*- coding: utf-8 -*-
"""
Created on Wed May 11 16:50:50 2022

@author: Marc Lopez
"""

# Cargamos las librerias necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
%matplotlib inline

## Librerias para los clusters
import scipy.cluster.hierarchy as shc
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score,accuracy_score
from sklearn.cluster import KMeans

from sklearn.tree import _tree, DecisionTreeClassifier

# =============================================================================
# Parámetros del modelo: 
#PATH = "E:\\DOCENCIA\\TFG Alumnos\\MARC LOPEZ\\REPOSITORIO\\"
#DATASETS_DIR = PATH + "data\\"

#-----------------------------------------------------------------------
#Load the data and look at the first few rows
PATH = "C:\\Users\marcl\\Desktop\\TFG\\GITHUB TFG\\"
DATASETS_DIR = PATH + "data\\"

# =============================================================================
# Cargamos la base de datos
hotelesNorm = pd.read_pickle(DATASETS_DIR + 'HotelesNormalizados.pkl')
hoteles = pd.read_pickle(DATASETS_DIR + 'HotelesImputados.pkl')

# =============================================================================
#Let’s first draw the dendrogram to help us 
#decide the number of clusters for this particular problem

plt.figure(figsize=(10, 7))  
plt.title("Dendrograms")  
dend = shc.dendrogram(shc.linkage(hotelesNorm, method='ward'))

silluete = []
kden = range(2, 7)

for k in kden:
    print("Realizamos agrupación de k = " + str(k))
    
    # Calculamos la clasificación con el número k 
    cluster = AgglomerativeClustering(n_clusters = k, affinity = 'euclidean', 
                                      linkage = 'ward')  
    # Predecimos el número de clases
    cluster.fit_predict(hotelesNorm)

    # Gráficamos el corte del dendograma
    plt.figure(figsize=(10, 7))  
    plt.title("Dendograma para k = " + str(k))  
    dend = shc.dendrogram(shc.linkage(hotelesNorm, method = 'ward', 
                                      metric = 'euclidean'), labels = cluster.labels_)
    plt.axhline(y = 6, color = 'r', linestyle = '--')

    # Graficamos dicho corte en las variables precio vs. distnacia en la variable original
    # plt.figure(figsize = (10, 7))  
    # plt.scatter(hotelesNorm['precio'], hotelesNorm['distancia'], 
    #            c = cluster.labels_) 
    # plt.xlabel('precios')
    # plt.ylabel('distancia')
    # plt.title('Clustering Jerárquico con k =' + str(k))
    # plt.legend(range(1, k + 1))

    # Calculamos el estadístico de sillhouete para ver cual es la mejor agrupación
    silluete.append(silhouette_score(hotelesNorm, cluster.labels_, metric = 'euclidean', 
                     random_state = 0))
    #printeamos el estadístico de sillhouete
    print("El estadístico de sillhouete para k = " + str(k) + " es: " + str(silluete[-1]))

# Graficamos el estadistico de la sillhouete
plt.plot(kden, silluete, '--bo', label = 'Sillhouette')

# Seleccionamos el mejor
kOptima = kden[np.argmax(silluete)] #me coge 6
#kOptima = 2 #est sillhouete o.431

# Calculamos la clasificación con el número k 
cluster = AgglomerativeClustering(n_clusters = kOptima, affinity = 'euclidean', 
                                  linkage = 'ward')  
# Predecimos el número de clases
cluster.fit_predict(hotelesNorm)

# Graficamos los valores de la mejor clasificación
plt.figure(figsize = (10, 7))  
plt.scatter(hotelesNorm['precio'], hotelesNorm['distancia'], 
            c = cluster.labels_) 
plt.xlabel('precio')
plt.ylabel('distancia')
plt.title('Clustering Jerárquico con k =' + str(kOptima))
plt.legend(range(0, kOptima))

# =============================================================================
###Adjusted Rand Index 
labels_pred = cluster.labels_
labels_true = hoteles['precio']
from sklearn.metrics.cluster import adjusted_rand_score
adjusted_rand_score(labels_true, labels_pred)

#------------------------------------------------------------------------------

################################################################################
###Bucle para realizar diferentes clusterings KMEANS 
#comparar COEFICIENTE DE SILHOUETTE

for k in range(2,8):
    #realizar el clustering
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(hotelesNorm)
    #calcular el silhouette score
    silhouette_avg = silhouette_score(hotelesNorm, kmeans.labels_)
    print("For n_clusters =", k, "The average silhouette_score is :", silhouette_avg)

#------------------------------------------------------------------------------
##Realizamos KMEANS con 2 clusters 
#porque el COEFICIENTE DE SILHOUETTE es demasiado similar entre grupos 
kmeans = KMeans(n_clusters = 2, init = 'k-means++', max_iter = 300,
                n_init = 10, random_state = 0)
kmeans.fit(hotelesNorm)
labels_pred = kmeans.labels_
labels_true = hoteles['precio']

# Graficamos los valores de la mejor clasificación
plt.figure(figsize = (10, 7))
plt.scatter(hotelesNorm['precio'], hotelesNorm['distancia'],
            c = kmeans.labels_) 
plt.xlabel('precios')
plt.ylabel('distancia')
plt.title('Clustering K-Means con k = 2')
plt.legend(range(1, kOptima + 1))

###PROFILING-------------------------------------------------------------------
df_features = hotelesNorm
# Add cluster labels
df_features['cluster_ids'] = kmeans.labels_

# Overall level summary
df_profile_overall = df_features.describe().T

# using mean; use appropriate summarization (median, count, etc.) for each feature
df_profile_overall['Overall Dataset'] = df_profile_overall[['mean']]
df_profile_overall = df_profile_overall[['Overall Dataset']]

# Cluster ID level summary
df_cluster_summary = df_features.groupby('cluster_ids').describe().T.reset_index()
df_cluster_summary = df_cluster_summary.rename(columns={'level_0':'column','level_1':'metric'})

# using mean; use appropriate summarization (median, count, etc.) for each feature
df_cluster_summary = df_cluster_summary[df_cluster_summary['metric'] == "mean"]
df_cluster_summary = df_cluster_summary.set_index('column')

# join into single summary dataset
df_profile = df_cluster_summary.join(df_profile_overall) # joins on Index

#cluster 0 == precios bajos, mucha distancia al mar 
#cluster 1 == precios medios altos, mas cerca del mar, mas habitaciones



# =================================================================================
# Definimos unas funciones que nos permitan describir nuestros datos

def get_class_rules(tree: DecisionTreeClassifier, feature_names: list):
  inner_tree: _tree.Tree = tree.tree_
  classes = tree.classes_
  class_rules_dict = dict()

  def tree_dfs(node_id=0, current_rule=[]):
    # feature[i] holds the feature to split on, for the internal node i.
    split_feature = inner_tree.feature[node_id]
    if split_feature != _tree.TREE_UNDEFINED: # internal node
      name = feature_names[split_feature]
      threshold = inner_tree.threshold[node_id]
      # left child
      left_rule = current_rule + ["({} <= {})".format(name, threshold)]
      tree_dfs(inner_tree.children_left[node_id], left_rule)
      # right child
      right_rule = current_rule + ["({} > {})".format(name, threshold)]
      tree_dfs(inner_tree.children_right[node_id], right_rule)
    else: # leaf
      dist = inner_tree.value[node_id][0]
      dist = dist/dist.sum()
      max_idx = dist.argmax()
      if len(current_rule) == 0:
        rule_string = "ALL"
      else:
        rule_string = " and ".join(current_rule)
      # register new rule to dictionary
      selected_class = classes[max_idx]
      class_probability = dist[max_idx]
      class_rules = class_rules_dict.get(selected_class, [])
      class_rules.append((rule_string, class_probability))
      class_rules_dict[selected_class] = class_rules
    
  tree_dfs() # start from root, node_id = 0
  return class_rules_dict

def cluster_report(data: pd.DataFrame, clusters, min_samples_leaf=50, pruning_level=0.01):
    # Create Model
    tree = DecisionTreeClassifier(min_samples_leaf=min_samples_leaf, ccp_alpha=pruning_level)
    tree.fit(data, clusters)
    
    # Generate Report
    feature_names = data.columns
    class_rule_dict = get_class_rules(tree, feature_names)

    report_class_list = []
    for class_name in class_rule_dict.keys():
        rule_list = class_rule_dict[class_name]
        combined_string = ""
        for rule in rule_list:
            combined_string += "[{}] {}\n\n".format(rule[1], rule[0])
        report_class_list.append((class_name, combined_string))
        
    cluster_instance_df = pd.Series(clusters).value_counts().reset_index()
    cluster_instance_df.columns = ['class_name', 'instance_count']
    report_df = pd.DataFrame(report_class_list, columns=['class_name', 'rule_list'])
    report_df = pd.merge(cluster_instance_df, report_df, on='class_name', how='left')
    return(report_df.sort_values(by='class_name')[['class_name', 'instance_count', 'rule_list']])


report = cluster_report(hotelesNorm, cluster.labels_)
print(report)