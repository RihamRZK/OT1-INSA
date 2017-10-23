<h1>Présentation de la structure du projet</h1>

Le projet se présente sous forme de notebook python, développé pour un cours de 5IF à l'INSA de Lyon.

L'équipe est composée de :
<ul>
	<li>Nathan Arsac</li>
	<li>Arij Daif</li>
	<li>Arnaud Dupeyrat</li>
	<li>Jacques Folléas</li>
	<li>Mathis Hammel</li>
	<li>Riham Razoki</li>
</ul>


<h2> But du projet </h2>

   Le projet consiste à mettre en place un outil de référencement permettant un accès efficace à de grands volumes de données textuelles. 
Il s’agit donc de s'initier aux différents algorithmes permettant de construire des index inversés , posting lists et le traitement des requêtes top-k ( naive algorithm , fagin’s algorithm , fagin’s threshold algorithm).

<h2> Structure du projet </h2>

Le projet se découpe en différents fichiers python représentants chacun une étape de la construction de l'outil de référencement.
Ces fichiers sont regroupés dans <b> ./src </b>: 

<ul>

<li><b>indexFile.ipynb</b> => notebook permettant d'exécuter les différents fichiers </li>
	 	
<li><b>util_index.py</b> => permettant d'effectuer le preprocessing des données, tokenization, stemming, stop-word removal permettant de construire des posting list plus petites.</li>
		
<li><b>util_posting.py</b> => TODO r</li>
	
<li><b>encoded_posting.py</b> => TODO</li>
		
<li><b>graph.py</b> => contenant le code pour la construction et l'affichage des graphs de performance</li>
		
<li><b>naive.py</b> => contenant l'implémentation du naive algorithm permettant de retourner les k objets ayant les meilleurs scores </li>
	
<li><b>faginsNaive.py</b> => contenant l'implémentation de fagin's algorithm permettant de retourner les k objets ayant les meilleurs scores  </li>
		
<li><b>fagins.py</b> => contenant l'implémentation de fagin's threshold algorithm permettant de retourner les k objets ayant les meilleurs scores  </li>

</ul>

L'ensemble des sauvegardes des fichiers intermédiaires se fait dans le dossier <b>./data</b> 
