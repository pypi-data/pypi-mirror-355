# %% Required modules
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


# %% parallelCoordinatesPlot function
def parallelCoordinatesPlot(
    filePath,
    numAssignments,
    startColIndex,
    normalize=True,
    replaceMissingWithZero=True,
    ydIndex=None,
):
    """This functions creates a parallel coordinates plot of student scores to
    visualize the point at which students start struggling.

    Parameters
    ----------
    filePath : Str
        Full path to the location of the Canvas gradebook file.
    numAssignments : Int
        The number of assignments for which you want to create box plots.
    startColIndex : Int
        The column index where the assignments start. This assumes that all
        of the assignment columns are adjacent.
    normalize : Bool
        Whether to convert the scores to a 0-1 scale so that assignments
        of differnt point values can be compared. The default is True.
    replaceMissingWithZero : Bool
        Whether to replace missing assignment scores with 0. The default is True.
    ydIndex : Int
        The column index for the yellowdig assignment, if there is one.

    Returns
    -------
    An interactive parallel coordinates plot of student scores.
    """
    df = pd.read_csv(filePath)

    # Extract only student name and homework columns
    colNums = [0]
    if ydIndex is not None:
        colNums.append(ydIndex)
    colNums.extend(list(range(startColIndex, startColIndex + numAssignments)))

    # Create new column names for homework assignments
    colNames = ["Student"]
    hwCols = ["h" + str(i) for i in range(1, numAssignments + 1)]
    if ydIndex is not None:
        hwCols.insert(0, "yd")
    colNames.extend(hwCols)
    df = df.iloc[:, colNums]
    df.columns = colNames

    # Calculate divisors, including a divisor for the total score
    divisors = df.iloc[
        0, 1:
    ]  # Get the first row, which contains the value of the assignments
    divisors = divisors.tolist()
    divisors.append(sum(divisors))

    # Create a total column that sums the scores for each student
    df["total"] = df.iloc[:, 1:].apply("sum", axis=1)

    # Remove the first row, which contains the assignment values
    df = df.iloc[1:, :]

    # Convert hw columns to numeric just in case they are not
    df[hwCols] = df[hwCols].apply(pd.to_numeric)

    # Loop through each row to calculate the percentage for each assignment
    if normalize:
        for c in range(1, df.shape[1]):
            df.iloc[:, c] = df.iloc[:, c] / divisors[c - 1]
    if replaceMissingWithZero:
        df = df.fillna(0)  # Fill in missing values with 0

    # Remove test student
    df = df.query('Student.str.contains("Test") == False')

    fig = px.parallel_coordinates(
        df, color="total", title="Parallel Coordinates Plot of Scores"
    )
    fig.show()


# %% tidyUpCols Function
def tidyUpCols(myList, keepNums=False):
    """
    Parameters
    ----------
    myList : List
        List of column names, like df.columns
    keepNums : Bool
        Whether we want to keep numbers in column names. The default is False.

    Returns
    -------
    ml2 : List
        List of tidy column names.
    """
    ml2 = []
    for i in range(len(myList)):
        if myList[i] != None:
            ti = (
                myList[i]
                .strip()
                .lower()
                .replace(".", "")
                .replace("/", "_")
                .replace(" ", "_")
                .replace("$", "")
            )
        else:
            continue  # Goes to the next iteration in the for loop

        if "--" in ti:
            ti2 = ti.split("--")
            [ml2.append(x) for x in ti2]
        elif keepNums == True:
            ti = re.sub("[^a-zA-Z_0-9]", "", ti)
            ml2.append(ti)
        else:
            ti = re.sub("[^a-zA-Z_]", "", ti)
            ml2.append(ti)
    return ml2


# %% assignmentPlots function
def assignmentPlots(
    filePath,
    numAssignments,
    startColIndex,
    normalize=True,
    replaceMissingWithZero=True,
    ydIndex=None,
):
    """
    This function uses an export from canvas to create boxplots and stripplots
    of assignments.

    Parameters
    ----------
    filePath : Str
        Full path to the location of the Canvas gradebook file.
    numAssignments : Int
        The number of assignments for which you want to create box plots.
    startColIndex : Int
        The column index where the assignments start. This assumes that all
        of the assignment columns are adjacent.
    normalize : Bool
        Whether to convert the scores to a 0-1 scale so that assignments
        of differnt point values can be compared. The default is True.
    replaceMissingWithZero : Bool
        Whether to replace missing assignment scores with 0. The default is True.
    ydIndex : Int
        The column index for the yellowdig assignment, if there is one.

    Returns
    -------
    A box and whisker plot on the left and a stripplot on the right.

    """
    df = pd.read_csv(filePath)

    # Extract only student name and homework columns
    colNums = [0]
    if ydIndex is not None:
        colNums.append(ydIndex)
    colNums.extend(list(range(startColIndex, startColIndex + numAssignments)))

    # Create new column names for homework assignments
    colNames = ["Student"]
    hwCols = ["h" + str(i) for i in range(1, numAssignments + 1)]
    if ydIndex is not None:
        hwCols.insert(0, "yd")
    colNames.extend(hwCols)
    df = df.iloc[:, colNums]
    df.columns = colNames

    # Calculate divisors, including a divisor for the total score
    divisors = df.iloc[
        0, 1:
    ]  # Get the first row, which contains the value of the assignments
    divisors = divisors.tolist()
    divisors.append(sum(divisors))

    # Create a total column that sums the scores for each student
    df["total"] = df.iloc[:, 1:].apply("sum", axis=1)

    # Remove the first row, which contains the assignment values
    df = df.iloc[1:, :]

    # Convert hw columns to numeric just in case they are not
    df[hwCols] = df[hwCols].apply(pd.to_numeric)

    # Loop through each row to calculate the percentage for each assignment
    if normalize:
        for c in range(1, df.shape[1]):
            df.iloc[:, c] = df.iloc[:, c] / divisors[c - 1]
    if replaceMissingWithZero:
        df = df.fillna(0)  # Fill in missing values with 0

    # Remove test student
    df = df.query('Student.str.contains("Test") == False')

    # Convert from wide to long
    hw = df.melt(value_vars=hwCols, var_name="Homework", value_name="Score")

    # Create canvas with two columns
    fig, axs = plt.subplots(figsize=(15, 5), ncols=2)
    fig.tight_layout(pad=2)

    # Boxplot on left side
    sns.boxplot(
        data=hw,
        x="Homework",
        y="Score",
        hue="Homework",
        ax=axs[0],
        showmeans=True,
        meanprops={"markeredgecolor": "black"},
    )
    axs[0].set_title("Boxplot of Homework Scores")

    # Stripplot on right side
    sns.stripplot(data=hw, x="Homework", y="Score", hue="Homework", ax=axs[1])
    axs[1].set_title("Stripplot of Homework Scores")


# Test out the function
# assignmentPlots('/Users/rnguymon/Downloads/htdy2.csv', 5, 9)


# %% relocate function
def relocate(df, old_index, new_index):
    """
    This function relocates one column of a dataframe based on index number.

    Parameters
    ----------
    df : Pandas dataframe
        This is the dataframe object that has a column you would like to
        relocate.
    old_index : INT
        This is th eindex number of the column that you want to relocate.
    new_index : INT
        This is the destination index number of the relocated column.

    Returns
    -------
    df : Pandas dataframe
        The same dataframe with the relocated column.

    """
    # Convert column names to a list, col_names
    col_names = df.columns.tolist()
    # Remove the column and insert it into a new location
    col_names.insert(new_index, col_names.pop(old_index))
    # Slice the dataframe using the col_names list
    df = df.loc[:, col_names]
    # Return the dataframe
    return df
