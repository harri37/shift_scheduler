# ITLC Shift scheduler
This is a integer programming model for schedulilng shifts at UQ's ITLC. The mathematical formulation is provided in `formulation.pdf`. Running the scheduler requires a gurobi license, which can be obtained from [Gurobi's website](https://www.gurobi.com/). To run the model, you can adjust the data variables in `main.py` and then run the script using:

```bash
python main.py
```