# Buko Forecaster

**Name:** Maroš Geffert  
**Email:** [xgeffe00@stud.fit.vutbr.cz](mailto:xgeffe00@stud.fit.vutbr.cz)  
**Thesis:** Framework for Event Modeling and Prediction in Football  
**Institution:** Brno University of Technology  
**Faculty:** Faculty of Information Technology

## Description
The Buko Forecaster is a sophisticated football match prediction software that utilizes advanced machine learning models and a variety of statistics to predict football match events. Designed to support football analysts, betting enthusiasts, and fans, this tool offers valuable insights into potential match events.

## Installation

### Prerequisites
Ensure that you have Python version 3.11 installed, as it is required for running the software.

<span style="color: red;">**Note:** Python 3.11 is required for this software.</span>

### Setup Script
Run the following script to set up the environment and dependencies:
```bash
./run_script_for_oponent.sh
```
**Note:** If the script fails to install any packages due to OS limitations, you will need to install them manually based on the error messages provided. The script includes config with an example prediction for 200 samples for the events 'goals over 2.5' and 'both teams scores'.

## Usage
To customize the software settings, such as changing the prediction model, adjusting the number of testing samples or some other features, edit the configuration file located at:
```plaintext
src/settings/experiment/oponent.yml
```

## Data
Data files are located in the `data` directory; however, only a small sample is included by default. To utilize the full capabilities of the software, you must provide your own comprehensive dataset. Obtain a data API key by purchasing a subscription from:
[API Football](https://www.api-football.com/)

Once you have your API key, you can generate your own dataset using the follwing script:
```plaintext
run/generate.sh
```

## Example program output
```
Leagues: bundesliga_germany | premier_league_england | serie_a_italy | la_liga_spain | 
Final budget: 108.22$ | Initial Budget: 100$ | ROI: 8.22%

Final results:
+----------+--------+----------+----------------------+-------------+-----------------+-----------------+----------------------+
| Accuracy | Brier  | F1 Score | Bookmaker Similarity | Average Odd | Win Average Odd | Scaled Accuracy | Avg Bookmaker margin |
+----------+--------+----------+----------------------+-------------+-----------------+-----------------+----------------------+
|  60.27   | 0.2321 |  0.7387  |        0.009         |    1.85     |      1.85       |      55.63      |         3.18         |
+----------+--------+----------+----------------------+-------------+-----------------+-----------------+----------------------+

Number of matches: 73
+------------+------------+--------+-----------+-------+--------------------------+--------+---------------------+--------+-----------+-----------+----------------+--------------+---------+---------+-----------------+------+--------+--------+
| fixture_id |    date    | season | league_id | ht_id |        home_team         | result |      away_team      | at_id  | odd_event | class_pst | complement_pst | chosen_class | ch_pred | outcome | expected_profit | odd  | co_odd | margin |
+------------+------------+--------+-----------+-------+--------------------------+--------+---------------------+--------+-----------+-----------+----------------+--------------+---------+---------+-----------------+------+--------+--------+
| 1038169.0  | 28-01-2024 |  2023  |    140    |  536  |         Sevilla          | 1 : 1  |       Osasuna       | 727.0  | btts_yes  |   0.52    |      0.48      |   btts_yes   |    1    |    1    |      0.13       | 2.16 |  1.75  |  3.44  |
| 1049044.0  | 28-01-2024 |  2023  |    78     |  182  |       Union Berlin       | 1 : 0  |   SV Darmstadt 98   | 181.0  | btts_yes  |   0.58    |      0.42      |   btts_yes   |    1    |    0    |      0.15       | 1.99 |  1.88  |  3.44  |
| 1052465.0  | 28-01-2024 |  2023  |    135    |  502  |        Fiorentina        | 0 : 1  |        Inter        | 505.0  | btts_yes  |   0.56    |      0.44      |   btts_yes   |    1    |    0    |      0.11       | 1.97 |  1.89  |  3.67  |
| 1052469.0  | 28-01-2024 |  2023  |    135    |  487  |          Lazio           | 0 : 0  |       Napoli        | 492.0  | btts_yes  |   0.53    |      0.47      |   btts_yes   |    1    |    0    |       0.1       | 2.08 |  1.81  |  3.33  |
| 1038165.0  | 29-01-2024 |  2023  |    140    |  546  |          Getafe          | 2 : 0  |     Granada CF      | 715.0  | btts_yes  |   0.55    |      0.45      |   btts_yes   |    1    |    0    |      0.21       | 2.21 |  1.72  |  3.39  |
| 1052472.0  | 29-01-2024 |  2023  |    135    |  514  |       Salernitana        | 1 : 2  |       AS Roma       | 497.0  | btts_yes  |   0.57    |      0.43      |   btts_yes   |    1    |    1    |      0.12       | 1.96 |  1.91  |  3.38  |
| 1035384.0  | 30-01-2024 |  2023  |    39     |  66   |       Aston Villa        | 1 : 3  |      Newcastle      |  34.0  | over_2.5  |   0.72    |      0.28      |   over_2.5   |    1    |    1    |      0.13       | 1.58 |  2.5   |  3.29  |
| 1035385.0  | 30-01-2024 |  2023  |    39     |  36   |          Fulham          | 0 : 0  |       Everton       |  45.0  | btts_yes  |   0.61    |      0.39      |   btts_yes   |    1    |    0    |      0.17       | 1.92 |  1.95  |  3.37  |
| 1035391.0  | 30-01-2024 |  2023  |    39     |  52   |      Crystal Palace      | 3 : 2  |    Sheffield Utd    |  62.0  | over_2.5  |   0.55    |      0.45      |   over_2.5   |    1    |    1    |      0.11       | 2.04 |  1.87  |  2.5   |
| 1035392.0  | 31-01-2024 |  2023  |    39     |  40   |        Liverpool         | 4 : 1  |       Chelsea       |  49.0  | over_2.5  |   0.76    |      0.24      |   over_2.5   |    1    |    1    |      0.14       | 1.49 |  2.73  |  3.74  |
| 1049087.0  | 24-02-2024 |  2023  |    78     |  172  |      VfB Stuttgart       | 1 : 1  |       FC Koln       | 192.0  | over_2.5  |   0.67    |      0.33      |   over_2.5   |    1    |    0    |      0.08       | 1.61 |  2.43  |  3.26  |
| 1052511.0  | 24-02-2024 |  2023  |    135    |  514  |       Salernitana        | 0 : 2  |        Monza        | 1579.0 | btts_yes  |   0.58    |      0.42      |   btts_yes   |    1    |    0    |      0.07       | 1.85 |  2.03  |  3.32  |
| 1038206.0  | 25-02-2024 |  2023  |    140    |  541  |       Real Madrid        | 1 : 0  |       Sevilla       | 536.0  | btts_yes  |   0.43    |      0.57      |   btts_no    |    0    |    0    |      0.11       | 1.94 |  1.91  |  3.9   |
| 1038209.0  | 25-02-2024 |  2023  |    140    |  534  |        Las Palmas        | 1 : 1  |       Osasuna       | 727.0  | btts_yes  |   0.56    |      0.44      |   btts_yes   |    1    |    1    |      0.18       | 2.1  |  1.79  |  3.48  |
| 1038211.0  | 25-02-2024 |  2023  |    140    |  543  |        Real Betis        | 3 : 1  |    Athletic Club    | 531.0  | btts_yes  |   0.56    |      0.44      |   btts_yes   |    1    |    1    |      0.09       | 1.95 |  1.92  |  3.37  |
| 1052456.0  | 28-02-2024 |  2023  |    135    |  505  |          Inter           | 4 : 0  |      Atalanta       | 499.0  | over_2.5  |   0.65    |      0.35      |   over_2.5   |    1    |    1    |      0.15       | 1.78 |  2.14  |  2.91  |
| 1035434.0  | 02-03-2024 |  2023  |    39     |  55   |        Brentford         | 2 : 2  |       Chelsea       |  49.0  | over_2.5  |   0.69    |      0.31      |   over_2.5   |    1    |    1    |      0.16       | 1.67 |  2.33  |  2.8   |
| 1035437.0  | 02-03-2024 |  2023  |    39     |  36   |          Fulham          | 3 : 0  |      Brighton       |  51.0  | over_2.5  |    0.7    |      0.3       |   over_2.5   |    1    |    1    |      0.28       | 1.83 |  2.05  |  3.43  |
| 1035440.0  | 02-03-2024 |  2023  |    39     |  34   |        Newcastle         | 3 : 0  |       Wolves        |  39.0  | over_2.5  |   0.68    |      0.32      |   over_2.5   |    1    |    1    |      0.05       | 1.56 |  2.58  |  2.86  |
| 1038214.0  | 02-03-2024 |  2023  |    140    |  546  |          Getafe          | 3 : 3  |     Las Palmas      | 534.0  | over_2.5  |   0.59    |      0.41      |   over_2.5   |    1    |    1    |       0.4       | 2.4  |  1.63  |  3.02  |
| 1052522.0  | 02-03-2024 |  2023  |    135    |  494  |         Udinese          | 1 : 1  |     Salernitana     | 514.0  | over_2.5  |   0.44    |      0.56      |  under_2.5   |    0    |    0    |      0.07       | 1.9  |  2.0   |  2.63  |
+------------+------------+--------+-----------+-------+--------------------------+--------+---------------------+--------+-----------+-----------+----------------+--------------+---------+---------+-----------------+------+--------+--------+
```