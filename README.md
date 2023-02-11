# eu4_dynamic_trade (alpha)

## How to use
 1. Install miniconda if you don't yet have Python. Preferably get Python version 3.8.
 2. Open settings.yaml
    1.1 Change file path to your game directory and your My Documents directory
    1.2 Specify the path and name of save game to use as reference for dynamic trade direction
    1.3 Adjust flow rules as needed. 3 possible flow rules are implemented. 
        The ordering is important. If the 1st rule is sufficient to break a tie between 2 nodes, no subsequent rule will be used, if not then rules are applied in order.
        So change the ordering according to your preference.
        - country_development: trade are pulled towards higher-development countries
        - total_development: trade are pulled towards node with higher total development
        - total_provincial_trade_power: trade are pulled towards node with higher total provincial trade power
    1.4 End node restriction restricts the number of end node to N_END_NODE. 
        Possible values are 'restricted' and 'unrestricted'
    1.5 RELOAD_SAVE_DATA is by default True. Can be set to False if your save data is the same as the last run of the script, to save time extracting save data.
 3. After changing settings, run 'Anaconda Prompt'.
 4. From Anaconda Prompt, navigate to the right directory and run 'python main.py' (without quote). 
    The python version used in development is 3.8. There should be no need for external library, otherwise run 'pip install (required library)', without quote and without parenthesis inside Anaconda Prompt (may require administrator privilege).   