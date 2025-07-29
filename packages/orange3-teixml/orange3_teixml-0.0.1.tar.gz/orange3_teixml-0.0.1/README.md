# orange3-teixml

This provides a collection of widgets for processing TEI-XML documents.

## Installation

Within the Add-ons installer, click on "Add more..." and type in orange3-teixml

## Widgets

  * **TEI Token Extractor**: Parses through TEI-XML files in a directory and extracts the words with annotations (like parts of speech) and counts the occurances.  It then takes the `N` most frequent words across all the documents and filters the results with those words.

> ⚠️ If you load TEI-XML documents from different sources, it is very likely that the annotation schemes are different and the tokens won't match.  In my examples below, "An abridgement of the English military discipline," was loaded from a different source.

## Screenshots

A screenshot of a simple Orange workflow with the TEI Token Extractor feeding a data table.

![A screenshot of a simple Orange workflow with the TEI Token Extractor feeding a data table.](imgs/TEI%20XML%20Token%20Extractor%20Workflow.png)  

The TEI Token Extractor widget set with the "inputs" directory selected, the number of top tokens set to 15, and the normalize checkbox cleared.

![The TEI Token Extractor widget set with the "inputs" directory selected, the number of top tokens set to 15, and the normalize checkbox cleared.](imgs/TEI%20Token%20Extractor%20Widget.png)

Data table with the counts of tokens for various Shakesphere works and An abdridgement of English military discipline.

![Data table with the counts of tokens for various Shakesphere works and An abdridgement of English military discipline.](imgs/Data%20Table%20with%20Counts.png)

Data table with the frequency of tokens for various Shakesphere works and An abdridgement of English military discipline.

![Data table with the frequency of tokens for various Shakesphere works and An abdridgement of English military discipline.](imgs/Data%20Table%20with%20Counts.png)