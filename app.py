from flask import Flask, render_template
import pandas as pd
import matplotlib.pyplot as plt

from io import BytesIO
import base64

import matplotlib

matplotlib.use('Agg')  # Указываем использовать бэкенд Agg для отрисовки графиков

app = Flask(__name__)


@app.route('/')
def plot_graph():
    # Чтение данных из CSV файла в DataFrame
    # df = pd.read_csv('data/test.csv', delimiter=',')
    df = pd.read_csv('data/com12_60s.csv', delimiter=',')

    signals = []

    start_row_index = 0

    for index, row in df.iterrows():
        if row['V_value'] == 0:
            if index != start_row_index:
                signal = df.iloc[start_row_index:index].to_dict(orient='list')
                signals.append(signal)
            start_row_index = index

    # Добавляем последний сигнал
    signal = df.iloc[start_row_index:].to_dict(orient='list')
    signals.append(signal)

    images_for_signals = {
        "voltage_pulse": [],
        "current_pulse": [],
        "WE_pulse": [],
    }

    current_ch0 = []
    current_ch1 = []
    Qch = []

    fig, ax = plt.subplots()

    for signal in signals:

        # current_measurements
        if len(signal["I_value"]) >= 3:
            last_three_values = signal["I_value"][-3:]
            current_measurement = int(round(sum(last_three_values) / 3000))
        else:
            current_measurement = None

        # split current_measurement by channel number
        if signal["Channel#"][1] == 0:
            current_ch0.append(current_measurement)
        elif signal["Channel#"][1] == 1:
            current_ch1.append(current_measurement)

        # superimposed I_value img creation
        y_values = signal["I_value"]
        y_values = [int(round(value / 1000)) for value in y_values]
        x_values = signal["Time"]

        # normalization of x_values
        min_value = min(x_values)
        max_value = max(x_values)
        new_min = 0
        new_max = 120
        normalized_x_values = [(x - min_value) / (max_value - min_value) * (new_max - new_min) + new_min for x in
                               x_values]

        # current density calculation
        electrode_area = 3.14 * 20
        current_density = [int(round(value / electrode_area)) for value in y_values]

        ax.plot(normalized_x_values, current_density, marker='o', linestyle='-', markersize=3)

        # calculation of a parameter Qch that is proportional to the charge
        # normalization of y_values
        min_y_value = min(y_values)
        normalized_y_values = [y - min_y_value for y in y_values]
        area = 0
        n = len(normalized_x_values)
        for i in range(1, n):
            h = normalized_x_values[i] - normalized_x_values[i - 1]
            area += 0.5 * (normalized_y_values[i] + normalized_y_values[i - 1]) * h

        Qch.append(area)

    plt.xlabel('Time as normalized_x_values')
    plt.ylabel('current_density')
    plt.grid(True)
    fig.set_figwidth(5)
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    plt.clf()
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML
    images_for_signals["current_pulse"].append(img_base64)

    plt.hist(Qch, bins=20, edgecolor='k')
    plt.xlabel('Qch')
    plt.ylabel('Events')
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    plt.clf()
    img_buf.seek(0)
    Qch_hist = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML

    # for signal in signals:
    #     # voltage_pulse image creation
    #     y_values = signal["V_value"]
    #     y_values = [int(round(value / 1000)) for value in y_values]
    #     x_values = signal["Time"]
    #     fig, ax = plt.subplots()
    #     ax.plot(x_values, y_values, marker='o', linestyle='-')
    #     plt.xlabel('Time')
    #     plt.ylabel('V_value')
    #     plt.grid(True)
    #     fig.set_figwidth(5)
    #     img_buf = BytesIO()  # Сохранение графика как изображения
    #     plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    #     plt.clf()
    #     img_buf.seek(0)
    #     img_base64 = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML
    #     images_for_signals["voltage_pulse"].append(img_base64)
    #
    #     # current_pulse image creation
    #     y_values = signal["I_value"]
    #     y_values = [int(round(value / 1000)) for value in y_values]
    #     fig, ax = plt.subplots()
    #     ax.plot(x_values, y_values, marker='o', linestyle='-')
    #     plt.xlabel('Time')
    #     plt.ylabel('I_value')
    #     plt.grid(True)
    #     fig.set_figwidth(5)
    #     img_buf = BytesIO()  # Сохранение графика как изображения
    #     plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    #     plt.clf()
    #     img_buf.seek(0)
    #     img_base64 = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML
    #     images_for_signals["current_pulse"].append(img_base64)
    #
    #     # WE_pulse image creation
    #     y_values = signal["WE_value"]
    #     y_values = [int(round(value / 1000)) for value in y_values]
    #     fig, ax = plt.subplots()
    #     ax.plot(x_values, y_values, marker='o', linestyle='-')
    #     plt.xlabel('Time')
    #     plt.ylabel('WE_value')
    #     plt.grid(True)
    #     fig.set_figwidth(5)
    #     img_buf = BytesIO()  # Сохранение графика как изображения
    #     plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    #     plt.clf()
    #     img_buf.seek(0)
    #     img_base64 = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML
    #     images_for_signals["WE_pulse"].append(img_base64)

    # list of indices for HTML loop
    max_images_for_signals_count = max(len(img) for img in images_for_signals.values())
    indices = list(range(max_images_for_signals_count))

    # current_ch0 and current_ch1 image creation
    print("current_ch0", current_ch0)
    print("current_ch1", current_ch1)
    indices_current_ch0 = list(range(len(current_ch0)))

    fig, ax = plt.subplots()
    ax.plot(indices_current_ch0, current_ch0, label='current_ch0', marker='o', linestyle='-', markersize=3)
    ax.plot(indices_current_ch0, current_ch1, label='current_ch1', marker='o', linestyle='-', markersize=3)
    plt.xlabel('index')
    plt.ylabel('current_measurement')
    plt.grid(True)
    fig.set_figwidth(5)
    img_buf = BytesIO()  # Сохранение графика как изображения
    plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
    plt.clf()
    img_buf.seek(0)
    image_for_current_measurements = base64.b64encode(img_buf.read()).decode()  # base64 needed for HTML

    return render_template('index.html', images_for_signals=images_for_signals, indices=indices,
                           image_for_current_measurements=image_for_current_measurements, Qch_hist=Qch_hist)


if __name__ == '__main__':
    app.run()
