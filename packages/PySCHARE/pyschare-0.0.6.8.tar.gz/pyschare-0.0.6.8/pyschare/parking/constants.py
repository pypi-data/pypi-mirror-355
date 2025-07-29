
VISUAL_TABLE: str = 'MainTableDatasetsDictionary_Visuals.csv'
MAIN_TABLE: str = 'MainTableDatasetsDictionary_2.csv'
MAIN_TABLE_VAR: str = 'dataset'
MAIN_TITLE: str = 'dataset_title'
DPATH: str = 'datasets'
FPATH: str = 'file_name'

DICTPATH: str = 'Dictionary_path'


visual_helper_text = "<p>Use the dropdown menus to select a dataset and configure your plot parameters.</p><ul><li><strong>Bar, count, box, boxen, strip, swarm, and violin plots</strong> typically require a categorical variable on the X-axis (or hue) and a numeric variable on the Y-axis; see the <a href='https://seaborn.pydata.org/tutorial/categorical.html' target='_blank'>categorical tutorial</a> for details.</li><li><strong>Scatter and line plots</strong> call for numeric variables on both axes (e.g., time vs. measurement); refer to the <a href='https://seaborn.pydata.org/tutorial/relational.html' target='_blank'> relational tutorial</a>.</li><li><strong>Histograms</strong> typically need a single numeric variable on the X-axis and are described in the <a href='https://seaborn.pydata.org/tutorial/distributions.html' target='_blank'> distributions tutorial</a>.</li></ul><p>Use <strong>“hue”</strong> to differentiate categories by color, <strong>“style”</strong> to vary markers or lines, and <strong>“size”</strong> to scale markers based on another variable. The <strong>“col” and “row”</strong> options create subplots (facets) for comparison across categories, while the <strong>“multiple”</strong> parameter (e.g., 'dodge,' 'stack,' 'fill') manages overlapping data displays. Once the plot type and settings are selected, click <strong>“Show Plot”</strong> to visualize the results.</p>"
select_helper_text = "<p>To view the dataset, use the <strong>Select Dataset</strong> dropdown and click the <strong>Show Data</strong> button. To save the displayed data, click the <strong>Save Data</strong> button. The confirmation that where data is saved will be shown below the Save Data button.</p><p> To clear both the confirmation message and the displayed data table, click the <strong>Clear Output</strong> button.</p>"

subset_helper_text = "<p>Use the <strong>Select Dataset</strong> dropdown to choose a dataset. The available variables will be dynamically populated when you select options in the <strong>Select Variables</strong> dropdown. After selecting the desired variables from the <strong>Select Variables</strong> dropdown, you may visualize the data by clicking the <strong>Show Data</strong> button. This will display the first few rows of the specific columns selected in the output area below.</p>     <p>To save the displayed data, click the <strong>Save Data</strong> button. This action will store the selected data in your bucket and confirm the successful operation in the output area. Please make sure you have made selections in both the dataset and variables dropdowns before attempting to save.</p>"

calculate_helper_text = f"""<p>This widget allows you to create various types of plots using your selected dataset. Follow the steps below to build your visualization:</p>

    <ol><li><strong>Choose a Dataset:</strong>
            <p>Begin by selecting a dataset from the "Select Dataset" dropdown menu. Click the dropdown to see the list of available datasets and choose the one you want to use.
            </p>
        </li><li>
            <strong>Select a Plot Type:</strong>
            <p>Next, choose the type of plot you want to create from the "Select Plot" dropdown menu. Common plot types include:
            </p>
            <ul>
                <li><strong>Bar Plots, Count Plots, Box Plots, Boxen Plots, Strip Plots, Swarm Plots, and Violin Plots:</strong> These are typically used to show relationships between categories. They usually require a categorical variable for the X-axis (or "Hue") and a numeric variable for the Y-axis. (See the <a href="link_to_categorical_tutorial">Categorical Tutorial</a> for more details).</li>
                <li><strong>Scatter Plots and Line Plots:</strong> These are used to show relationships between two numeric variables. For example, you might plot time versus measurement. (See the <a href="link_to_relational_tutorial">Relational Tutorial</a> for more details).</li>
                <li><strong>Histograms:</strong> These are used to show the distribution of a single numeric variable. (See the <a href="link_to_distributions_tutorial">Distributions Tutorial</a> for more details).</li>
            </ul>
        </li>

        <li>
            <strong>Configure Plot Parameters:</strong>
            <p>
                <ul>
                    <li><strong>X-Axis and Y-Axis:</strong> Use the "Select X" and "Select Y" dropdown menus to choose the variables you want to plot on the X and Y axes. The available options will depend on the dataset you selected.</li>
                    <li><strong>Hue:</strong> Use the "Select Hue" dropdown to color-code your data points based on categories. This helps to visualize how different categories are distributed.</li>
                    <li><strong>Style:</strong> Use the "Select Style" dropdown to vary the markers or lines in your plot, based on categories.</li>
                    <li><strong>Size:</strong> Use the "Select Size" dropdown to scale the size of the markers based on another variable.</li>
                    <li><strong>Column and Row:</strong> Use the "Select Column" and "Select Row" dropdowns to create subplots (facets). This allows you to compare different categories across multiple plots.</li>
                    <li><strong>Layer (Multiple):</strong> Use the "Select Layer" dropdown to manage how overlapping data points are displayed. Options like "Dodge," "Stack," and "Fill" are available.</li>
                </ul>
            </p>
        </li>

        <li>
            <strong>View Your Plot:</strong>
            <p>
                Once you have selected your plot type and configured the parameters, click the "Show Plot" button. Your plot will be displayed below the widget.
            </p>
        </li>

        <li>
            <strong>Clear Output:</strong>
            <p>
                To clear the displayed plot, click the "Clear Output" button.
            </p>
        </li>
    </ol>
    """

data_explore_helper_text = f"""<p>This widget allows you to explore and manipulate datasets. Follow the steps below to work with the data:</p>
    <ol><li><strong>Selecting a Dataset:</strong>
            <p>Use the "Select Dataset" dropdown menu to choose the dataset you want to work with. Click on the dropdown to see a list of available datasets and select your choice.
            </p></li><li><strong>Selecting Variables:</strong>
            <p>After selecting a dataset, the "Select Variable" dropdown menu will populate with a list of variables available within that dataset.
                Choose the variables from the "Select Variable" dropdown you want to analyze. You can select multiple variables from this dropdown.
                (<em>Note:</em> If you do not select any variables, actions will be applied to all variables).
            </p></li><li><strong>Viewing Data:</strong>
            <p>To view the first few rows of the selected dataset or the selected variables, click the "Show Data" button. The results will be displayed in the output area below the widget.
            </p></li>
        <li><strong>Describing Data:</strong>
            <p>To view summary statistics (like mean, median, standard deviation) for the selected variables, click the "Describe Data" button.
                The summary statistics will be shown in the output area below the widget.
                If you haven't selected any variables, statistics for all variables in the dataset will be displayed.
            </p></li><li><strong>Saving Data:</strong>
            <p>To save the displayed data (either the entire dataset or the subset of selected variables), click the "Save Data" button.
                A confirmation message, including the location where the data is saved, will be displayed in the output area below the buttons.
                <br>
                <em>Note:</em> Ensure you have selected a dataset and, if applicable, variables before clicking "Save Data."
            </p></li><li><strong>Clearing Output:</strong>
            <p>To clear both the confirmation message (from saving) and the displayed data table or statistics in the output area, click the "Clear Output" button.
            </p></li></ol>
"""


search_helper_text = f"""<p>This widget allows you to search for variables and descriptions across multiple datasets. Follow these instructions to effectively use the search functionality:
        <li><strong>If you want to search within a specific dataset:</strong> Use the "Datasets" dropdown menu to select the dataset you wish to search. Scroll down to see the list of available datasets and select your choice.
        </li><li><strong>If you want to search across all datasets:</strong>Leave the "Datasets" dropdown set to "None". This is the default option.
        </li>In the text box, type the word or phrase you want to search for and click the "Search" button. Note: You need to enter at least 3 characters for the search to function.</p>
        <p><strong>Search Results:</strong> The widget will display a table below the search box, showing the search results.
        <li><strong>If a specific dataset was selected:</strong> The table will show the variables and descriptions from that dataset that match your search terms.
        </li><li><strong>If "None" was selected:</strong> The table will show results from all datasets that match your search terms, including the dataset name, variable name, and description.
        </li></p><p><strong>Save Table:</strong> If you want to save the search results as an HTML file, click the "Save Table" button.
        <li><strong>If a specific dataset was selected:</strong> The file will be named using the dataset name and the search terms (e.g., "Food Security Data 2021_searchterm.html").
        </li><li><strong>If "None" was selected:</strong> The file will be named using "Datasets" and the search terms (e.g., "Datasets_with_searchterm.html").
        </li>A confirmation message will appear below the "Save Table" button, indicating the file name and location.</p>"""

datafacts_helper=f"""<p>Please provide the Project Title for this dataset. This title serves as the primary label for identification and citation purposes.
In the Project Description field, enter a detailed abstract or summary. This description should clearly outline the dataset's main objectives, scope, and content (such as key variables or topics covered). If applicable, include a brief summary of the methodology and potential areas for application or research.
Once done, press the 'Save' button to generate the dataset facts summary. </p>"""

metatable_helper=f"""<p>This section is designated for capturing comprehensive metadata – structured information that describes, explains, locates, or otherwise makes it easier to retrieve, use, or manage the dataset. Please complete the following fields with accurate and relevant information pertaining to your dataset.
</p><p> Providing detailed metadata is essential for ensuring the dataset adheres to principles of findability, accessibility, interoperability, and reusability (<em>FAIR</em>). Complete and accurate metadata significantly enhances the dataset's value by facilitating discovery, enabling proper interpretation and analysis, ensuring correct citation, and promoting responsible reuse within the community.
Key metadata elements often cover areas such as:
<li>
<strong>Identification:</strong> <code>Filename</code>, <code>URL</code> </li>
<li><strong>Format &amp; Structure:</strong> <code>Format</code>, <code>Rows</code>, <code>Columns</code>, <code>CDEs</code> (Common Data Elements), <code>Missing</code> data information</li>
<li><strong>Context &amp; Scope:</strong> <code>Domain</code>, <code>Keywords</code>, <code>Type</code>, <code>Geography</code>, <code>Description</code></li>
<li><strong>Methodology:</strong> <code>Data Collection Method</code>, <code>Time Method</code>, <code>Data Collection Timeline</code></li>
<li><strong>Administration &amp; Access:</strong> <code>License</code>, <code>Released</code> date, <code>Funding Agency</code></li>
</ul>
After completing the applicable fields, click the 'Save' button to commit the metadata and render it in a structured tabular format for review.</p>"""

provenance_helper=f"""<p>
  Please document the origin and authorship of this dataset by providing information about both the 
  <code>Source</code> and the <code>Author(s)</code>. For the Source, enter details about the entity responsible for the data's creation or 
  distribution (e.g., Institution Name, Project Name, Repository), including its <code>URL</code> 
  and a contact <code>Email</code> address if available. For the Author(s), include information about the individual creator(s) involved 
  (e.g., Name, Affiliation, ORCID iD).Once you have entered these details, click the <strong>"Save"</strong> button. This will record the 
  provenance data and generate a table summarizing the dataset's lineage for review.
</p>"""


dictionary_helper=f"""
    <p> A data dictionary provides essential definitions for each variable within your dataset 
        (e.g., variable names, detailed descriptions, units of measurement, coding schemes for categorical data).
  Before uploading, prepare your data dictionary as a CSV (Comma Separated Values) file. Ensure this file contains 
            at least two columns: one listing the exact <strong>variable names</strong> as they appear in your dataset, 
            and another providing their corresponding <strong>descriptions</strong> or definitions. Click the <strong>"Upload Data Dictionary"</strong> button and select your prepared CSV file from your system.
After uploading, you may be prompted to confirm which columns in your file correspond to the 
            'Variable Name' and 'Description' fields required by the system.
        Upon successful upload and mapping, a structured table detailing your dataset's variables and their 
        definitions will be generated based on the information in your dictionary file.
    </p>
"""


stats_helper=f"""
    <p>This section calculates and displays summary statistics for the variables in your dataset. To ensure 
        that appropriate statistical measures are computed for each variable, you must first classify the variables 
        according to their measurement scale (nominal, ordinal, discrete, continuous). To generate the summary statistics:
    <ol><li><strong>Upload/Confirm Dataset:</strong> Ensure your dataset (in CSV format) is loaded. You can use the 
            <strong>"Show Data"</strong> button to preview the data and verify variable names if needed.
        </li><li>
            <strong>Classify Variables by Type:</strong> Based on the nature of each variable in your dataset, input 
            its exact name into the corresponding classification field below. Separate multiple variable names within 
            a single category using commas (e.g., <code>Variable_a, Variable_b, Variable_c</code>).
            <ul>
                <li><strong>Ordinal Variables:</strong> Categorical variables with a meaningful order (e.g., education level: High School, Bachelor's, Master's).</li>
                <li><strong>Nominal Variables:</strong> Categorical variables without an inherent order (e.g., Country, Eye Color).</li>
                <li><strong>Continuous Variables:</strong> Numerical variables that can take any value within a given range (e.g., Temperature, Height).</li>
                <li><strong>Discrete Variables:</strong> Numerical variables that can only take specific, distinct values, often integers (e.g., Number of Children, Page Visits).</li>
            </ul></li>
        <li><strong>Generate Statistics:</strong> After assigning variables to their respective types, click the 
            <strong>"Show Statistics Table"</strong> button.
        </li></ol>
        The system will then generate and display a table containing relevant descriptive statistics tailored 
        to each variable's classification (e.g., frequency counts and percentages for nominal/ordinal; mean, median, 
        standard deviation, min/max for continuous/discrete).
    </p>
"""


bar_plot_helper = f"""
    <p>
        Bar plots display the frequency or count of observations for each category within your selected 
      categorical variables. This helps in understanding the distribution across different categories. Select one, two, or up to three categorical variables (nominal or ordinal) 
        from the dropdown menus provided. The corresponding bar plot(s) will automatically generate or update below as you make or change 
        your selections, illustrating the frequency for each category within the chosen variable(s).
    </p>
"""


plot_helper= f"""
    <p>To explore the relationship between any two variables from your dataset, choose two variables using the dropdown menus.   Pair plots that visualize the distributions and relationships between the chosen pair of variables will automatically generate or update in the space below as you make your selections. </p>"""

correlation_helper=f""" <p>A correlation heatmap provides a visual summary of the association matrix between selected variables. 
    Using color intensity, it illustrates the strength and direction of these associations, helping to identify patterns in your data.
Choose the variables you wish to include in the analysis from the provided lists. The heatmap automatically calculates and visualizes the appropriate measure of association based on the types of variables being compared:
<ul>
    <li>For pairs of <strong>continuous variables</strong>, it calculates <strong>Pearson's correlation coefficient (r)</strong> to measure linear association.</li>
    <li>For pairs of <strong>categorical variables</strong>, it calculates <strong>Cramér's V</strong> to measure the strength of association.</li>
    <li>For pairs involving one <strong>continuous</strong> and one <strong>categorical</strong> variable, it calculates <strong>Pearson's correlation coefficient (r)</strong>. <em>(Note: The categorical variable is automatically converted into numerical format using dummy coding for this calculation.)</em></li>
</ul>
The resulting heatmap will automatically generate or update below as you select or deselect variables.
</p>"""


metadata = {
    "Filename": "",
    "Format": "",
    "Study/Project URL": "",
    "Domain": "",
    "Keywords": "",
    "Type": "",
    "Geography": "",
    "Data Collection Method": "",
    "Time Method": "",
    "Rows": "",
    "Columns": "",
    "CDEs": "",
    "Missing": "",
    "License": "",
    "Released": (None),
    "Data Collection Timeline": (None, None),
    "Funding Agency":"",
    "Description": ""
}

output_names = ['facts', 'meta', 'pro', 'corr_plot', 'pair_plot', 'bars', 'stats', 'show_data', 'var']

button_labels = ['pro', 'meta', 'facts']

field_names = ['Project Title','Project Description', 'Filename', 'Format', 'URL','Domain','Keywords','Type', 'Geography' , 'Data Collection Method', 'Time Method', 'Rows',
               'Columns','CDEs', 'Missing','License', 'Released', 'Funding Agency', 'Description', 'Source Name', 'Source URL', 'Source Email', 'Author Name', 'Author URL', 'Author Email']




