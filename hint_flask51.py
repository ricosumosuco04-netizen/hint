from flask import (
    Flask,
    request,
    render_template_string,
    session,
    redirect,
    url_for,
)
import os
import hmac
import html
import json


# =========================================================
# Flask
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-secret-key-for-test"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# =========================================================
# パスワード
# =========================================================

def get_app_password():
    return os.environ.get("APP_PASSWORD", "")


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ひっ算 ヒントカード</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
    background: #eaf7fa;
    color: #263238;
}

.login-container {
    width: 100%;
    max-width: 430px;
    padding: 20px;
}

.login-title {
    text-align: center;
    font-size: 30px;
    font-weight: bold;
    color: #24415a;
    margin-bottom: 28px;
}

.login-card {
    background: white;
    border-radius: 22px;
    padding: 28px 22px;
    box-shadow: 0 4px 16px rgba(0,0,0,.08);
}

.login-card h2 {
    margin-top: 0;
    text-align: center;
    font-size: 22px;
}

.login-message {
    text-align: center;
    color: #607d8b;
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 22px;
}

.password-input {
    width: 100%;
    padding: 16px;
    border: 2px solid #ccd8dd;
    border-radius: 14px;
    font-size: 20px;
    text-align: center;
}

.login-button {
    width: 100%;
    margin-top: 16px;
    padding: 17px;
    border: none;
    border-radius: 15px;
    background: #f0a93c;
    color: white;
    font-size: 19px;
    font-weight: bold;
}

.login-error {
    padding: 12px;
    margin-bottom: 16px;
    border-radius: 12px;
    background: #ffe2e2;
    color: #a32222;
    text-align: center;
    font-weight: bold;
}

.setting-error {
    padding: 14px;
    border-radius: 12px;
    background: #fff3cd;
    line-height: 1.7;
    text-align: center;
}
</style>
</head>

<body>
<div class="login-container">
    <div class="login-title">ひっ算 ヒントカード</div>

    <div class="login-card">
        {% if no_password %}

        <div class="setting-error">
            パスワードがまだ設定されていません。
        </div>

        {% else %}

        <h2>パスワードを いれてください</h2>

        <div class="login-message">
            ヒントカードを見るには<br>
            パスワードがひつようです。
        </div>

        {% if error %}
        <div class="login-error">
            パスワードが ちがいます。
        </div>
        {% endif %}

        <form method="post">
            <input
                class="password-input"
                type="password"
                name="password"
                placeholder="パスワード"
                required
            >

            <button class="login-button" type="submit">
                入る
            </button>
        </form>

        {% endif %}
    </div>
</div>
</body>
</html>
"""


@app.route("/login", methods=["GET", "POST"])
def login():
    password = get_app_password()
    no_password = not bool(password)
    error = False

    if request.method == "POST":
        entered = request.form.get("password", "")

        if password and hmac.compare_digest(entered, password):
            session["logged_in"] = True
            return redirect(url_for("home"))

        error = True

    return render_template_string(
        LOGIN_PAGE,
        error=error,
        no_password=no_password,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================================================
# 数とくらい
# =========================================================

def digits(n):
    """百・十・一のくらいの数字を返す"""
    return n // 100, (n // 10) % 10, n % 10


def place_count(n1, n2):
    """どちらかが3桁なら3列、それ以外は2列"""
    return 3 if max(n1, n2) >= 100 else 2


# =========================================================
# ●・■・100のまとまり
# =========================================================

def circles(n):
    if n <= 0:
        return '<span class="none">なし</span>'

    return "".join(
        '<span class="circle"></span>'
        for _ in range(n)
    )


def squares(n):
    if n <= 0:
        return '<span class="none">なし</span>'

    return "".join(
        '<span class="square"></span>'
        for _ in range(n)
    )


def hundreds_blocks(n):
    if n <= 0:
        return '<span class="none">なし</span>'

    return "".join(
        '<span class="hundred-block">100</span>'
        for _ in range(n)
    )


def legend_html(include_hundred=True):
    """凡例の順番を必ず ● → ■ → 100 に統一"""
    html = """
    <div class="legend">
        <div class="legend-row">
            <span class="circle"></span>
            <span>＝ 1</span>
        </div>

        <div class="legend-row">
            <span class="square"></span>
            <span>＝ 10のまとまり</span>
        </div>
    """

    if include_hundred:
        html += """
        <div class="legend-row">
            <span class="hundred-block mini">100</span>
            <span>＝ 100のまとまり</span>
        </div>
        """

    html += "</div>"

    return html


# =========================================================
# 問題のひっさん
# =========================================================

def problem_html(n1, n2, sign):
    display_sign = "＋" if sign == "+" else "－"

    return f"""
    <div class="problem-card">

        <div class="problem-number">
            {n1}
        </div>

        <div class="problem-row">

            <span class="problem-sign">
                {display_sign}
            </span>

            <span class="problem-number">
                {n2}
            </span>

        </div>

        <div class="problem-line"></div>

    </div>
    """


# =========================================================
# くらいのおへや
# =========================================================

def room_html(n1, n2):
    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    if place_count(n1, n2) == 3:

        places = [
            ("百のくらいのおへや", 100, h1, h2, "hundreds"),
            ("十のくらいのおへや", 10, t1, t2, "tens"),
            ("一のくらいのおへや", 1, o1, o2, "ones"),
        ]

        grid_class = "room-3"

        decomposition = f"""
        <div>
            <b>{n1}</b>
            ＝ {h1 * 100} ＋ {t1 * 10} ＋ {o1}
        </div>

        <div>
            <b>{n2}</b>
            ＝ {h2 * 100} ＋ {t2 * 10} ＋ {o2}
        </div>
        """

        legend = legend_html(True)

    else:

        places = [
            ("十のくらいのおへや", 10, t1, t2, "tens"),
            ("一のくらいのおへや", 1, o1, o2, "ones"),
        ]

        grid_class = "room-2"

        decomposition = f"""
        <div>
            <b>{n1}</b>
            ＝ {t1 * 10} ＋ {o1}
        </div>

        <div>
            <b>{n2}</b>
            ＝ {t2 * 10} ＋ {o2}
        </div>
        """

        # 2桁でも、凡例は ● → ■ → 100 の順で統一
        legend = legend_html(True)

    headers = ""
    row1 = ""
    row2 = ""
    counts = ""

    for label, unit, d1, d2, kind in places:

        headers += f"""
        <div class="room-head">
            {label}
        </div>
        """

        if kind == "hundreds":
            symbols1 = hundreds_blocks(d1)
            symbols2 = hundreds_blocks(d2)

        elif kind == "tens":
            symbols1 = squares(d1)
            symbols2 = squares(d2)

        else:
            symbols1 = circles(d1)
            symbols2 = circles(d2)

        row1 += f"""
        <div class="room-cell">

            <div class="value-row">

                <span class="value-label">
                    {d1 * unit} ＝
                </span>

                <span class="symbol-area">
                    {symbols1}
                </span>

            </div>

        </div>
        """

        row2 += f"""
        <div class="room-cell">

            <div class="value-row">

                <span class="value-label">
                    {d2 * unit} ＝
                </span>

                <span class="symbol-area">
                    {symbols2}
                </span>

            </div>

        </div>
        """

        counts += f"""
        <div class="room-count">
            {unit}が{d1}こ
            <br>
            {unit}が{d2}こ
        </div>
        """

    return f"""
    {legend}

    <div class="decomposition">
        {decomposition}
    </div>

    <div class="room-table {grid_class}">
        {headers}
        {row1}
        {row2}
        {counts}
    </div>
    """


# =========================================================
# くらいがわからない
# =========================================================

def hint_place(n1, n2, mode):
    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    if mode == "sim":

        return f"""
        <h2>
            くらいを ぜんたいでみるヒント
        </h2>

        {room_html(n1, n2)}

        <div class="message">
            ★ 同じ「くらいのおへや」どうしが
            <br>
            たてに そろっているね！
        </div>

        <p class="big-message">
            同じくらいどうしを 見てみよう！
        </p>
        """

    steps = [
        (
            "まず いちばんみぎを見る",
            f"{o1} と {o2}",
            "一のくらい",
        ),
        (
            "つぎに そのひだりを見る",
            f"{t1} と {t2}",
            "十のくらい",
        ),
    ]

    if place_count(n1, n2) == 3:
        steps.append(
            (
                "さいごに そのひだりを見る",
                f"{h1} と {h2}",
                "百のくらい",
            )
        )

    html = """
    <h2>
        くらいを じゅんばんでみるヒント
    </h2>
    """

    for index, (title, numbers, place_name) in enumerate(steps, 1):

        html += f"""
        <div class="step">

            <span class="step-number">
                {index}
            </span>

            <div>
                <b>{title}</b>

                <br><br>

                {numbers}

                <br>
                ↓
                <br>

                <b>{place_name}</b>
            </div>

        </div>
        """

    html += """
    <div class="message">
        ★ 同じくらいどうしが
        たてにそろっているか
        たしかめよう！
    </div>
    """

    return html


# =========================================================
# どこからやるかわからない
# =========================================================

def hint_start(n1, n2, sign, mode):
    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    display_sign = "＋" if sign == "+" else "－"

    if place_count(n1, n2) == 3:

        places = [
            ("百のくらい", h1, h2),
            ("十のくらい", t1, t2),
            ("一のくらい", o1, o2),
        ]

        cols = 3

    else:

        places = [
            ("十のくらい", t1, t2),
            ("一のくらい", o1, o2),
        ]

        cols = 2

    if mode == "sim":

        headers = ""
        numbers = ""
        orders = ""

        order_map = {
            label: index
            for index, (label, top, bottom)
            in enumerate(reversed(places), 1)
        }

        for label, top, bottom in places:

            headers += f"""
            <div class="start-title">
                {label}
            </div>
            """

            numbers += f"""
            <div class="start-number">
                {top}
                <br>

                <span class="small-sign">
                    {display_sign}
                </span>

                {bottom}
            </div>
            """

            number = order_map[label]

            text = (
                "まずここ！"
                if number == 1
                else "つぎ！"
            )

            orders += f"""
            <div class="order">

                <span>
                    {number}
                </span>

                <div class="down-arrow">
                    ↓
                </div>

                <b>
                    {text}
                </b>

            </div>
            """

        flow = " → ".join(
            place[0]
            for place in reversed(places)
        )

        return f"""
        <h2>
            どこから？
            ぜんたいでみるヒント
        </h2>

        <div class="start-grid cols-{cols}">
            {headers}
            {numbers}
            {orders}
        </div>

        <div class="flow">
            {flow}
        </div>

        <div class="message">
            ★ ひっ算は、
            いちばんみぎの
            <br>
            「一のくらい」から はじめるよ！
        </div>
        """

    steps = [
        "一のくらいを 計算する",
        "くり上がり・くり下がりが あるか たしかめる",
        "十のくらいを 計算する",
    ]

    if place_count(n1, n2) == 3:
        steps.append(
            "百のくらいを 計算する"
        )

    html = """
    <h2>
        どこから？
        じゅんばんでみるヒント
    </h2>
    """

    for index, step in enumerate(steps, 1):

        html += f"""
        <div class="step">

            <span class="step-number">
                {index}
            </span>

            <div>
                {step}
            </div>

        </div>
        """

    return html


# =========================================================
# 足し算の計算処理
# =========================================================

def addition_process(n1, n2):
    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    ones_total = o1 + o2
    carry_to_tens = ones_total // 10
    ones_answer = ones_total % 10

    tens_total = (
        t1
        + t2
        + carry_to_tens
    )

    carry_to_hundreds = (
        tens_total // 10
    )

    tens_answer = (
        tens_total % 10
    )

    hundreds_total = (
        h1
        + h2
        + carry_to_hundreds
    )

    return {
        "h1": h1,
        "t1": t1,
        "o1": o1,
        "h2": h2,
        "t2": t2,
        "o2": o2,
        "ones_total": ones_total,
        "carry_to_tens": carry_to_tens,
        "ones_answer": ones_answer,
        "tens_total": tens_total,
        "carry_to_hundreds": carry_to_hundreds,
        "tens_answer": tens_answer,
        "hundreds_total": hundreds_total,
    }


# =========================================================
# 一のくらいの視覚的なくり上がり
# =========================================================

def visual_carry_ones(s):
    if s["carry_to_tens"]:

        return f"""
        <div class="visual-stage">

            <div class="stage-title">
                まず、一のくらいを見てみよう！
            </div>

            <div class="visual-operation">

                <div>
                    {circles(s["o1"])}
                </div>

                <div class="big-operator">
                    ＋
                </div>

                <div>
                    {circles(s["o2"])}
                </div>

            </div>

            <div class="equation">
                {s["o1"]} ＋ {s["o2"]} ＝ {s["ones_total"]}
            </div>

            <div class="message">
                ●が
                <b>{s["ones_total"]}こ</b>
                あるね！
            </div>

            <div class="group-box">

                <div class="stage-title">
                    この10こを 見てみよう
                </div>

                <div class="symbol-line">
                    {circles(10)}
                </div>

                <div class="down-arrow-big">
                    ↓
                </div>

                <span class="square big-square"></span>

                <div class="relation">
                    ●が10こ ＝ ■が1こ
                </div>

            </div>

            <div class="remaining-box">

                <div class="stage-title">
                    のこりは
                </div>

                <div>
                    {circles(s["ones_answer"])}
                </div>

                <div class="relation">
                    ●が{s["ones_answer"]}こ
                </div>

            </div>

            <div class="move-grid">

                <div class="move-card">
                    <span class="square big-square"></span>

                    <div class="down-arrow-big">
                        ↓
                    </div>

                    <b>
                        十のくらいへ
                    </b>
                </div>

                <div class="move-card">
                    {circles(s["ones_answer"])}

                    <div class="down-arrow-big">
                        ↓
                    </div>

                    <b>
                        一のくらいに のこる
                    </b>
                </div>

            </div>

            <div class="message">
                ★「1が10こ」は
                <br>
                「10が1こ」と 同じだね！
            </div>

        </div>
        """

    return f"""
    <div class="visual-stage">

        <div class="stage-title">
            まず、一のくらいを見てみよう！
        </div>

        <div class="visual-operation">

            <div>
                {circles(s["o1"])}
            </div>

            <div class="big-operator">
                ＋
            </div>

            <div>
                {circles(s["o2"])}
            </div>

        </div>

        <div class="equation">
            {s["o1"]} ＋ {s["o2"]} ＝ {s["ones_total"]}
        </div>

        <div class="message">
            ●が{s["ones_total"]}こ
            <br><br>
            ★ 10こにならないので、
            くり上がりは ないよ！
        </div>

    </div>
    """


# =========================================================
# 十のくらいの視覚的なくり上がり
# =========================================================

def visual_carry_tens(s):
    """
    ご希望どおり、

          ■■■
           ＋
          ■■
           ＋
      一のくらいからくり上がった■

    のように縦にそろえて表示する。
    くり上がった■も同じ大きさ。
    """

    carry_row = ""

    if s["carry_to_tens"]:
        carry_row = """
        <div class="op-plus">
            ＋
        </div>

        <div class="op-carry-row">
            <span>
                一のくらいから くり上がった
            </span>
            <span class="square"></span>
        </div>
        """

    if s["carry_to_hundreds"]:

        return f"""
        <div class="visual-stage">

            <div class="stage-title">
                つぎに、十のくらいを見てみよう！
            </div>

            <div class="vertical-operation">

                <div class="op-symbol-row">
                    {squares(s["t1"])}
                </div>

                <div class="op-plus">
                    ＋
                </div>

                <div class="op-symbol-row">
                    {squares(s["t2"])}
                </div>

                {carry_row}

            </div>

            <div class="equation">
                {s["t1"]}
                ＋
                {s["t2"]}
                {" ＋ 1" if s["carry_to_tens"] else ""}
                ＝
                {s["tens_total"]}
            </div>

            <div class="message">
                ■が
                <b>{s["tens_total"]}こ</b>
                あるね！
            </div>

            <div class="group-box">

                <div class="stage-title">
                    この10こを まとめてみよう
                </div>

                <div class="symbol-line">
                    {squares(10)}
                </div>

                <div class="down-arrow-big">
                    ↓
                </div>

                <span class="hundred-block">
                    100
                </span>

                <div class="relation">
                    ■が10こ ＝ 100が1こ
                </div>

            </div>

            <div class="remaining-box">

                <div class="stage-title">
                    十のくらいに のこるのは
                </div>

                {squares(s["tens_answer"])}

                <div class="relation">
                    ■が{s["tens_answer"]}こ
                </div>

            </div>

            <div class="move-grid">

                <div class="move-card">

                    <span class="hundred-block">
                        100
                    </span>

                    <div class="down-arrow-big">
                        ↓
                    </div>

                    <b>
                        百のくらいへ
                    </b>

                </div>

                <div class="move-card">

                    {squares(s["tens_answer"])}

                    <div class="down-arrow-big">
                        ↓
                    </div>

                    <b>
                        十のくらいに のこる
                    </b>

                </div>

            </div>

            <div class="message">
                ★「10が10こ」は
                <br>
                「100が1こ」と 同じだね！
            </div>

        </div>
        """

    return f"""
    <div class="visual-stage">

        <div class="stage-title">
            つぎに、十のくらいを見てみよう！
        </div>

        <div class="vertical-operation">

            <div class="op-symbol-row">
                {squares(s["t1"])}
            </div>

            <div class="op-plus">
                ＋
            </div>

            <div class="op-symbol-row">
                {squares(s["t2"])}
            </div>

            {carry_row}

        </div>

        <div class="equation">
            {s["t1"]}
            ＋
            {s["t2"]}
            {" ＋ 1" if s["carry_to_tens"] else ""}
            ＝
            {s["tens_total"]}
        </div>

        <div class="message">
            ■が{s["tens_total"]}こ
            <br><br>
            ★ 10こにならないので、
            百のくらいへの くり上がりは ないよ！
        </div>

    </div>
    """


# =========================================================
# くり上がり
# =========================================================

def hint_carry_add(n1, n2, mode):
    s = addition_process(n1, n2)

    if mode == "sim":

        html = """
        <h2>
            くり上がりを ぜんたいでみるヒント
        </h2>
        """

        # 凡例は ● → ■ → 100 に統一
        html += legend_html(True)

        html += visual_carry_ones(s)

        if (
            place_count(n1, n2) == 3
            or
            s["carry_to_hundreds"]
        ):
            html += visual_carry_tens(s)

        if place_count(n1, n2) == 3:

            extra_hundred = ""

            if s["carry_to_hundreds"]:
                extra_hundred = """
                <span class="big-operator">
                    ＋
                </span>

                <span class="hundred-block">
                    100
                </span>
                """

            html += f"""
            <div class="visual-stage">

                <div class="stage-title">
                    さいごに、百のくらいを見てみよう！
                </div>

                <div class="hundreds-summary">

                    {hundreds_blocks(s["h1"])}

                    <span class="big-operator">
                        ＋
                    </span>

                    {hundreds_blocks(s["h2"])}

                    {extra_hundred}

                </div>

                <div class="message">
                    百のくらいまで
                    つながっているね！
                </div>

            </div>
            """

        return html

    # -------------------------
    # じゅんばんでみる
    # -------------------------

    steps = []

    steps.append(
        f'一のくらい：'
        f'{s["o1"]} ＋ '
        f'{s["o2"]} ＝ '
        f'{s["ones_total"]}'
    )

    if s["carry_to_tens"]:

        steps.append(
            f'一のくらいに '
            f'{s["ones_answer"]} '
            f'を書いて、'
            f'十のくらいへ 1 '
            f'くり上げる'
        )

    else:

        steps.append(
            f'一のくらいに '
            f'{s["ones_answer"]} '
            f'を書く'
        )

    tens_expression = (
        f'{s["t1"]} ＋ '
        f'{s["t2"]}'
    )

    if s["carry_to_tens"]:
        tens_expression += " ＋ 1"

    steps.append(
        f'十のくらい：'
        f'{tens_expression} '
        f'＝ '
        f'{s["tens_total"]}'
    )

    if s["carry_to_hundreds"]:

        steps.append(
            f'十のくらいに '
            f'{s["tens_answer"]} '
            f'を書いて、'
            f'百のくらいへ 1 '
            f'くり上げる'
        )

    else:

        steps.append(
            f'十のくらいに '
            f'{s["tens_answer"]} '
            f'を書く'
        )

    if (
        place_count(n1, n2) == 3
        or
        s["carry_to_hundreds"]
    ):

        hundreds_expression = (
            f'{s["h1"]} ＋ '
            f'{s["h2"]}'
        )

        if s["carry_to_hundreds"]:
            hundreds_expression += " ＋ 1"

        steps.append(
            f'百のくらい：'
            f'{hundreds_expression} '
            f'＝ '
            f'{s["hundreds_total"]}'
        )

    html = """
    <h2>
        くり上がりを じゅんばんでみるヒント
    </h2>
    """

    for index, step in enumerate(steps, 1):

        html += f"""
        <div class="step">

            <span class="step-number">
                {index}
            </span>

            <div>
                {step}
            </div>

        </div>
        """

    return html


# =========================================================
# 引き算のくり下がり処理
# =========================================================

def subtraction_process(n1, n2):
    """
    一のくらいから考えたときに、
    実際にどう借りるかを計算しておく。
    """

    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    h = h1
    t = t1
    o = o1

    ones_needs_borrow = (
        o1 < o2
    )

    borrowed_hundred_for_ones = False
    borrowed_ten_for_ones = False

    # 一のくらいで引けない
    if ones_needs_borrow:

        # 十のくらいが0なら、まず百→十
        if t == 0:

            if h > 0:
                h -= 1
                t += 10
                borrowed_hundred_for_ones = True

        # 十→一
        if t > 0:
            t -= 1
            o += 10
            borrowed_ten_for_ones = True

    tens_after_ones_borrow = t

    tens_needs_borrow = (
        t < t2
    )

    borrowed_hundred_for_tens = False

    # 一のくらいの処理後、十のくらいで引けなければ百→十
    if tens_needs_borrow:

        if h > 0:
            h -= 1
            t += 10
            borrowed_hundred_for_tens = True

    return {
        "h1": h1,
        "t1": t1,
        "o1": o1,

        "h2": h2,
        "t2": t2,
        "o2": o2,

        "h": h,
        "t": t,
        "o": o,

        "ones_needs_borrow":
            ones_needs_borrow,

        "borrowed_hundred_for_ones":
            borrowed_hundred_for_ones,

        "borrowed_ten_for_ones":
            borrowed_ten_for_ones,

        "tens_after_ones_borrow":
            tens_after_ones_borrow,

        "tens_needs_borrow":
            tens_needs_borrow,

        "borrowed_hundred_for_tens":
            borrowed_hundred_for_tens,
    }


# =========================================================
# くり下がり・全体で見る
# =========================================================

def hint_borrow_sim(n1, n2):
    """
    デザインはユーザー指定の形：
    ・凡例
    ・必要なら短い説明ボックス
    ・百→十の変換
    ・十→一の変換
    ・借りた後の確認を横3列
      左から 百・十・一
      ＝右から読むと 一・十・百
    """

    p = subtraction_process(n1, n2)

    html = """
    <h2>
        くり下がりを ぜんたいでみるヒント
    </h2>
    """

    html += legend_html(True)

    # -----------------------------------------------------
    # 一のくらいで借りる必要がない
    # -----------------------------------------------------

    if not p["ones_needs_borrow"]:

        html += f"""
        <div class="message">
            一のくらいの
            {p["o1"]} － {p["o2"]} は
            そのまま計算できるね。
        </div>
        """

        # 十のくらいだけで借りる必要がある場合
        if p["tens_needs_borrow"]:

            html += f"""
            <div class="borrow-notice">
                一のくらいを見たあと、
                十のくらいの
                {p["tens_after_ones_borrow"]} － {p["t2"]}
                はそのままではできないね。
                百のくらいから十のくらいへ 1つかりよう。
            </div>

            <div class="borrow-visual-card">

                <div class="stage-title">
                    百のくらいから まとまりを1つ使うと…
                </div>

                <span class="hundred-block">
                    100
                </span>

                <div class="down-arrow-big">
                    ↓
                </div>

                <div class="symbol-line">
                    {squares(10)}
                </div>

                <div class="relation">
                    100が1こ ＝ ■が10こ
                </div>

            </div>
            """

    # -----------------------------------------------------
    # 一のくらいで借りる必要がある
    # -----------------------------------------------------

    else:

        #
        # 205-159 のように十のくらいが0
        #

        if p["borrowed_hundred_for_ones"]:

            html += f"""
            <div class="borrow-notice">

                一のくらいの
                {p["o1"]} － {p["o2"]} は
                そのままではできないね。

                <br><br>

                十のくらいから 1つかりたいけど、
                十のくらいは 0 だから、
                そのままでは 一のくらいへ
                かりられないよ。

                <br><br>

                まず 百のくらいから
                十のくらいへ 1つ うつそう。

            </div>


            <div class="borrow-visual-card">

                <div class="stage-title">
                    百のくらいから まとまりを1つ使うと…
                </div>

                <span class="hundred-block">
                    100
                </span>

                <div class="down-arrow-big">
                    ↓
                </div>

                <div class="symbol-line">
                    {squares(10)}
                </div>

                <div class="relation">
                    100が1こ ＝ ■が10こ
                </div>

            </div>


            <div class="borrow-visual-card">

                <div class="stage-title">
                    十のくらいから まとまりを1つ使うと…
                </div>

                <span class="square big-square"></span>

                <div class="down-arrow-big">
                    ↓
                </div>

                <div class="symbol-line">
                    {circles(10)}
                </div>

                <div class="relation">
                    ■が1こ ＝ ●が10こ
                </div>

            </div>
            """

        #
        # 255-159 のように、まず十→一
        #

        else:

            html += f"""
            <div class="borrow-notice">

                一のくらいの
                {p["o1"]} － {p["o2"]} は
                そのままではできないね。

                <br><br>

                十のくらいから
                一のくらいへ 1つかりよう。

            </div>


            <div class="borrow-visual-card">

                <div class="stage-title">
                    十のくらいから まとまりを1つ使うと…
                </div>

                <span class="square big-square"></span>

                <div class="down-arrow-big">
                    ↓
                </div>

                <div class="symbol-line">
                    {circles(10)}
                </div>

                <div class="relation">
                    ■が1こ ＝ ●が10こ
                </div>

            </div>
            """

            #
            # その結果、十のくらいも引けなくなった
            #

            if p["borrowed_hundred_for_tens"]:

                html += f"""
                <div class="borrow-notice">

                    一のくらいへ 1つかしたので、
                    十のくらいは
                    {p["t1"]} から
                    {p["tens_after_ones_borrow"]}
                    になったね。

                    <br><br>

                    だから今度は
                    十のくらいの
                    {p["tens_after_ones_borrow"]}
                    －
                    {p["t2"]}
                    がそのままではできないよ。

                    <br><br>

                    百のくらいから
                    十のくらいへ 1つかりよう。

                </div>


                <div class="borrow-visual-card">

                    <div class="stage-title">
                        百のくらいから まとまりを1つ使うと…
                    </div>

                    <span class="hundred-block">
                        100
                    </span>

                    <div class="down-arrow-big">
                        ↓
                    </div>

                    <div class="symbol-line">
                        {squares(10)}
                    </div>

                    <div class="relation">
                        100が1こ ＝ ■が10こ
                    </div>

                </div>
                """

    # -----------------------------------------------------
    # 借りた後の確認
    # -----------------------------------------------------

    html += f"""
    <div class="borrow-check-wrap">

        <div class="borrow-check-title">
            かりた あとの かくにんをしよう
        </div>

        <div class="borrow-check-row">

            <div class="borrow-check-card">
                <div class="borrow-place">
                    百のくらい
                </div>

                <div class="borrow-calc">
                    {p["h"]} － {p["h2"]}
                </div>

                <div class="borrow-think">
                    を考える
                </div>
            </div>


            <div class="borrow-check-card">
                <div class="borrow-place">
                    十のくらい
                </div>

                <div class="borrow-calc">
                    {p["t"]} － {p["t2"]}
                </div>

                <div class="borrow-think">
                    を考える
                </div>
            </div>


            <div class="borrow-check-card">
                <div class="borrow-place">
                    一のくらい
                </div>

                <div class="borrow-calc">
                    {p["o"]} － {p["o2"]}
                </div>

                <div class="borrow-think">
                    を考える
                </div>
            </div>

        </div>

    </div>
    """

    return html


# =========================================================
# くり下がり・順番で見る
# =========================================================

def hint_borrow_seq(n1, n2):
    p = subtraction_process(n1, n2)

    steps = []

    # 必ず一のくらいから
    if p["ones_needs_borrow"]:

        steps.append(
            f'一のくらい：'
            f'{p["o1"]} － '
            f'{p["o2"]} はそのままではできない'
        )

        if p["borrowed_hundred_for_ones"]:

            steps.append(
                '十のくらいのまとまりを使いたいが、'
                '十のくらいが0なのでまとまりを使えない'
            )

            steps.append(
                '百のくらいから十のくらいへ '
                'まとまりを1つ使う'
            )

        steps.append(
            '十のくらいから一のくらいへ '
            'まとまりを1つ使う'
        )

    else:

        steps.append(
            f'一のくらい：'
            f'{p["o1"]} － '
            f'{p["o2"]} を計算する'
        )

    steps.append(
        f'一のくらい：'
        f'{p["o"]} － '
        f'{p["o2"]} を計算する'
    )

    if p["tens_needs_borrow"]:

        steps.append(
            f'十のくらい：'
            f'{p["tens_after_ones_borrow"]} － '
            f'{p["t2"]} はそのままではできない'
        )

        steps.append(
            '百のくらいから十のくらいへ '
            'まとまりを1つ使う'
        )

    steps.append(
        f'十のくらい：'
        f'{p["t"]} － '
        f'{p["t2"]} を計算する'
    )

    if place_count(n1, n2) == 3:

        steps.append(
            f'百のくらい：'
            f'{p["h"]} － '
            f'{p["h2"]} を計算する'
        )

    html = """
    <h2>
        くり下がりを じゅんばんでみるヒント
    </h2>
    """

    for index, step in enumerate(steps, 1):

        html += f"""
        <div class="step">

            <span class="step-number">
                {index}
            </span>

            <div>
                {step}
            </div>

        </div>
        """

    return html


def hint_borrow_sub(n1, n2, mode):
    if mode == "sim":
        return hint_borrow_sim(n1, n2)

    return hint_borrow_seq(n1, n2)


# =========================================================
# ぜんぶむずかしい
# =========================================================

def hint_all(n1, n2, sign, mode):

    # -----------------------------------------------------
    # ぜんぶむずかしい × ぜんたいでみる
    # ※ ここはこれまでの表示をそのまま使用する
    # -----------------------------------------------------
    if mode == "sim":
        title = (
            "ぜんぶを "
            "ぜんたいでみるヒント"
        )

        if sign == "+":
            calculation_hint = (
                hint_carry_add(
                    n1,
                    n2,
                    mode
                )
            )

        else:
            calculation_hint = (
                hint_borrow_sub(
                    n1,
                    n2,
                    mode
                )
            )

        return f"""
        <h2>
            {title}
        </h2>

        {room_html(n1, n2)}

        <div class="message">
            ★ まず一のくらいから。
            <br>
            くらいをそろえて、
            右から左へ すすめよう！
        </div>

        <div class="subhint">
            {calculation_hint}
        </div>
        """

    # -----------------------------------------------------
    # ぜんぶむずかしい × じゅんばんでみる
    #
    # 「くらいを確認する → 一のくらいから始める → 計算する」
    # という1本の流れにし、各画面では1つの手順だけを
    # 見られるようにする。
    # -----------------------------------------------------

    h1, t1, o1 = digits(n1)
    h2, t2, o2 = digits(n2)

    steps = []

    # まずくらいを右から順番に確認する
    steps.append(
        f'<b>くらいを かくにんしよう</b><br><br>'
        f'いちばんみぎの {o1} と {o2} は、'
        f'<b>一のくらい</b>だよ。'
    )

    steps.append(
        f'<b>つぎのくらいを かくにんしよう</b><br><br>'
        f'そのひだりの {t1} と {t2} は、'
        f'<b>十のくらい</b>だよ。'
    )

    if place_count(n1, n2) == 3:
        steps.append(
            f'<b>さいごのくらいを かくにんしよう</b><br><br>'
            f'そのひだりの {h1} と {h2} は、'
            f'<b>百のくらい</b>だよ。'
        )

    # 計算を始めるくらい置を確認する
    steps.append(
        '<b>どこから はじめる？</b><br><br>'
        'まず、いちばんみぎの '
        '<b>一のくらい</b>から 計算しよう。'
    )

    # 足し算
    if sign == "+":
        s = addition_process(n1, n2)

        steps.append(
            f'<b>一のくらいを 計算しよう</b><br><br>'
            f'{s["o1"]} ＋ {s["o2"]} ＝ {s["ones_total"]}'
        )

        if s["carry_to_tens"]:
            steps.append(
                f'<b>くり上がりを かくにんしよう</b><br><br>'
                f'{s["ones_total"]} は、10と{s["ones_answer"]}。<br>'
                f'{s["ones_answer"]}を 一のくらいに書いて、'
                f'1を 十のくらいへ くり上げよう。'
            )
        else:
            steps.append(
                f'<b>一のくらいに 書こう</b><br><br>'
                f'{s["ones_answer"]}を 一のくらいに 書こう。<br>'
                f'くり上がりは ないよ。'
            )

        tens_expression = (
            f'{s["t1"]} ＋ {s["t2"]}'
        )

        if s["carry_to_tens"]:
            tens_expression += " ＋ 1"

        steps.append(
            f'<b>十のくらいを 計算しよう</b><br><br>'
            f'{tens_expression} ＝ {s["tens_total"]}'
        )

        if s["carry_to_hundreds"]:
            steps.append(
                f'<b>くり上がりを かくにんしよう</b><br><br>'
                f'{s["tens_total"]} は、10と{s["tens_answer"]}。<br>'
                f'{s["tens_answer"]}を 十のくらいに書いて、'
                f'1を 百のくらいへ くり上げよう。'
            )
        else:
            steps.append(
                f'<b>十のくらいに 書こう</b><br><br>'
                f'{s["tens_answer"]}を 十のくらいに 書こう。'
            )

        if (
            place_count(n1, n2) == 3
            or
            s["carry_to_hundreds"]
        ):
            hundreds_expression = (
                f'{s["h1"]} ＋ {s["h2"]}'
            )

            if s["carry_to_hundreds"]:
                hundreds_expression += " ＋ 1"

            steps.append(
                f'<b>百のくらいを 計算しよう</b><br><br>'
                f'{hundreds_expression} ＝ {s["hundreds_total"]}'
            )

    # 引き算
    else:
        p = subtraction_process(n1, n2)

        if p["ones_needs_borrow"]:
            steps.append(
                f'<b>一のくらいを 見てみよう</b><br><br>'
                f'{p["o1"]} － {p["o2"]} は '
                f'そのままでは できないね。'
            )

            if p["borrowed_hundred_for_ones"]:
                steps.append(
                    '<b>十のくらいを 見てみよう</b><br><br>'
                    '十のくらいから 1つかりたいけど、'
                    '十のくらいが0なので そのままでは かりられないよ。'
                )

                steps.append(
                    '<b>百のくらいから かりよう</b><br><br>'
                    '百のくらいから 十のくらいへ 1つかりよう。'
                )

            steps.append(
                '<b>十のくらいから かりよう</b><br><br>'
                '十のくらいから 一のくらいへ 1つかりよう。'
            )

        steps.append(
            f'<b>一のくらいを 計算しよう</b><br><br>'
            f'{p["o"]} － {p["o2"]} を 計算しよう。'
        )

        if p["tens_needs_borrow"]:
            steps.append(
                f'<b>十のくらいを 見てみよう</b><br><br>'
                f'{p["tens_after_ones_borrow"]} － {p["t2"]} は '
                f'そのままでは できないね。'
            )

            steps.append(
                '<b>百のくらいから かりよう</b><br><br>'
                '百のくらいから 十のくらいへ 1つかりよう。'
            )

        steps.append(
            f'<b>十のくらいを 計算しよう</b><br><br>'
            f'{p["t"]} － {p["t2"]} を 計算しよう。'
        )

        if place_count(n1, n2) == 3:
            steps.append(
                f'<b>百のくらいを 計算しよう</b><br><br>'
                f'{p["h"]} － {p["h2"]} を 計算しよう。'
            )

    html = """
    <h2>
        ぜんぶを じゅんばんでみるヒント
    </h2>
    """

    for index, step in enumerate(steps, 1):
        html += f"""
        <div class="step">

            <span class="step-number">
                {index}
            </span>

            <div>
                {step}
            </div>

        </div>
        """

    html += """
    <div class="message">
        ★ 一のくらいから じゅんばんに
        すすめられたね！
    </div>
    """

    return html


# =========================================================
# 児童が操作するヒント
# =========================================================

def interactive_hint(n1, n2, sign, trouble, mode):
    """Create hint-only tasks; the application's arithmetic and answer stay intact."""
    place_names = {1: "一のくらい", 10: "十のくらい", 100: "百のくらい", 1000: "千のくらい"}
    units = [1, 10] + ([100] if place_count(n1, n2) == 3 else [])
    display_units = units + ([units[-1] * 10] if sign == "+" and n1 + n2 >= units[-1] * 10 else [])
    top = {u: n1 // u % 10 for u in (1, 10, 100, 1000)}
    bottom = {u: n2 // u % 10 for u in (1, 10, 100, 1000)}
    steps = []
    answer_cards = mode == "sim" and trouble in ("place", "all")

    def add(kind, question, answer, **extra):
        steps.append(dict(kind=kind, question=question, answer=str(answer), **extra))

    if trouble == "place":
        for row, number in (("top", n1), ("bottom", n2)):
            for unit in reversed(units):
                digit = number // unit % 10
                label = "1" if unit == 1 else f"{unit}のまとまり"
                add("decomp_input" if mode == "sim" else "number",
                    f"{number}は、{label}が いくつある？", digit,
                    row=row, unit=unit, card=str(digit), focus=str(number))
        if mode == "sim":
            for row, number in (("top", n1), ("bottom", n2)):
                for unit in reversed(units):
                    digit = number // unit % 10
                    add("place_card", f"{number}の 数字カード {digit}を おへやへ おこう。",
                        f"{row}-{unit}", row=row, unit=unit, card=str(digit))

    if trouble == "all":
        for row, number in (("top", n1), ("bottom", n2)):
            for unit in reversed(units):
                digit = number // unit % 10
                label = "1" if unit == 1 else f"{unit}のまとまり"
                add("decomp_input" if mode == "sim" else "number",
                    f"{number}は、{label}が いくつある？", digit,
                    row=row, unit=unit, card=str(digit), focus=str(number))
        if mode == "sim":
            for row, number in (("top", n1), ("bottom", n2)):
                for unit in reversed(units):
                    digit = number // unit % 10
                    add("place_card", f"{number}の 数字カード {digit}を おへやへ おこう。",
                        f"{row}-{unit}", row=row, unit=unit, card=str(digit))

    if trouble in ("start", "all"):
        for order, unit in enumerate(units, 1):
            if mode == "sim":
                add("order_card", f"{order}ばんめの カードを くらいの下へ おこう。",
                    str(unit), unit=unit, card="①②③"[order - 1])
            else:
                add("choice", f"{order}ばんめに けいさんするのは どこ？",
                    place_names[unit], options=[place_names[u] for u in units],
                    focus=f"{order}ばんめ", unit=unit)

    if trouble in ("start", "carry", "all") or answer_cards or (trouble == "place" and mode == "seq"):
        if sign == "+":
            carry = 0
            for unit in units:
                if mode == "seq" and trouble in ("place", "all"):
                    add("choice", f"{n1 // unit % 10}と{n2 // unit % 10}は なんのくらい？",
                        place_names[unit], options=[place_names[u] for u in units],
                        unit=unit, place_pair=True)
                a, b = top[unit], bottom[unit]
                total = a + b + carry
                expression = f"{a}＋{b}" + ("＋1" if carry else "")
                add("number", f"{place_names[unit]}を けいさんしよう。{expression}＝□",
                    total, unit=unit, expression=expression, result=True, notice=("10のまとまりができたので、十のくらいへうつそう。" if carry and unit == 10 else "上のくらいへ まとまりを うつしたよ。" if carry else ""))
                calculation_step = len(steps) - 1
                if total >= 10 and trouble in ("carry", "all"):
                    if mode == "sim":
                        add("group", "10のまとまりを つくろう！", 10,
                            unit=unit, total=total)
                        add("move", "できた まとまりを つぎのくらいの おへやへ うつそう。",
                            str(unit * 10), unit=unit, target=unit * 10)
                    else:
                        add("number", "{entered}の中に 10のまとまりは いくつ？", 1,
                            unit=unit, reflect=calculation_step)
                        if unit * 10 <= 100:
                            add("choice", "10のまとまりは どこの おへやへ うつす？",
                                place_names[unit * 10], options=[place_names[u] for u in (1, 10, 100)],
                                unit=unit)
                    add("number", f"{place_names[unit]}に のこるのは いくつ？",
                        total % 10, unit=unit, focus=f"{total}から10こを まとめる")
                if answer_cards:
                    add("result_card", f"{place_names[unit]}の 答えカードを 同じくらいの おへやへ おこう。",
                        f"result-{unit}", unit=unit, card=str(total % 10))
                carry = total // 10
            if carry:
                add("number", f"{place_names[units[-1] * 10]}に いくつ ある？",
                    carry, unit=units[-1] * 10, result=True)
                if answer_cards:
                    unit = units[-1] * 10
                    add("result_card", f"{place_names[unit]}の 答えカードを 同じくらいの おへやへ おこう。",
                        f"result-{unit}", unit=unit, card=str(carry))
        else:
            for unit in units:
                if mode == "seq" and trouble in ("place", "all"):
                    add("choice", f"{n1 // unit % 10}と{n2 // unit % 10}は なんのくらい？",
                        place_names[unit], options=[place_names[u] for u in units],
                        unit=unit, place_pair=True)
                a, b = top[unit], bottom[unit]
                if a < b:
                    add("choice", f"{a}－{b}は、そのままで けいさんできる？",
                        "できない", options=["できる", "できない"], unit=unit)
                    upper = unit * 10
                    if top[upper] == 0:
                        add("choice", f"{place_names[upper]}の まとまりは ある？",
                            "ない", options=["ある", "ない"], unit=upper)
                        source = upper * 10
                        if mode == "sim":
                            add("break", f"{place_names[source]}の まとまりを 1こ ばらして {place_names[upper]}へ うつそう。",
                                f"{source}-{upper}", source=source, target=upper)
                        else:
                            add("number", f"{source}のまとまり1こを ばらすと、{upper}のまとまりは いくつ？",
                                10, unit=upper, focus=f"{source}のまとまり 1こ")
                        top[source] -= 1
                        top[upper] += 10
                    if mode == "sim":
                        add("break", f"{place_names[upper]}の まとまりを 1こ ばらして {place_names[unit]}へ うつそう。",
                            f"{upper}-{unit}", source=upper, target=unit)
                    else:
                        add("number", "1は いくつできる？" if unit == 1 else f"{upper}のまとまり1こを ばらすと、{unit}のまとまりは いくつ？",
                            10, unit=unit, focus=f"{upper}のまとまり 1こ")
                    top[upper] -= 1
                    top[unit] += 10
                    add("number", "ひかれる数は いくつ？" if mode == "sim" and unit == 1 else f"{place_names[unit]}は いくつに なった？",
                        top[unit], unit=unit, focus=f"{a}と、ふえた10こ")
                    add("number", f"{place_names[upper]}の まとまりは いくつ のこる？",
                        top[upper], unit=upper)
                expression = f"{top[unit]}－{b}"
                add("number", f"{place_names[unit]}を けいさんしよう。{expression}＝□",
                    top[unit] - b, unit=unit, expression=expression, result=True)
                if answer_cards:
                    add("result_card", f"{place_names[unit]}の 答えカードを 同じくらいの おへやへ おこう。",
                        f"result-{unit}", unit=unit, card=str(top[unit] - b))

    if mode == "sim":
        steps = [s for s in steps if s["kind"] == "decomp_input"] + [s for s in steps if s["kind"] != "decomp_input"]

    title = {"place": "くらい", "start": "どこから？", "carry": "くり上がり・くり下がり", "all": "ぜんぶ"}[trouble]
    title += "を ぜんたいでみるヒント" if mode == "sim" else "を じゅんばんでみるヒント"
    payload = dict(n1=n1, n2=n2, sign=sign, trouble=trouble, mode=mode,
                   units=units, display_units=display_units, steps=steps)
    data = html.escape(json.dumps(payload, ensure_ascii=False), quote=True)
    return (f'<div class="interactive-hint" data-hint="{data}">'
            f'<h2>{html.escape(title)}</h2>'
            '<div class="hint-interactive-body"></div>'
            '<div class="hint-navigation">'
            '<button type="button" class="seq-next-button hint-back">もどる</button>'
            '<button type="button" class="seq-next-button hint-next">つぎへ</button>'
            '</div></div>')


# =========================================================
# 答え確認
# =========================================================

def answer_top_marks(n1, n2, sign):
    # Display-only record; the existing calculation and answer are unchanged.
    top = {u: n1 // u % 10 for u in (1, 10, 100, 1000)}
    red, cross, carry = {}, set(), 0
    for u in (1, 10, 100):
        if sign == "+":
            carry = (top[u] + n2 // u % 10 + carry) // 10
            if carry:
                red[u * 10] = carry
        elif top[u] < n2 // u % 10:
            source = u * 10
            while top[source] == 0:
                source *= 10
            while source > u:
                top[source] -= 1
                cross.add(source)
                red[source] = top[source]
                top[source // 10] += 10
                red[source // 10] = 10
                source //= 10
    units = [10 ** i for i in range(max(len(str(n1)), len(str(n2))))][::-1]
    if red.get(units[0] * 10):
        units.insert(0, units[0] * 10)
    return "".join('<span class="answer-digit' + (' answer-cross' if u in cross else '') + '">' +
                   ('<small class="answer-red">' + str(red[u]) + '</small>' if u in red else '') +
                   (str(n1 // u % 10) if n1 >= u else '') + '</span>' for u in units)


def answer_html(n1, n2, sign):
    answer = (
        n1 + n2
        if sign == "+"
        else n1 - n2
    )

    display_sign = (
        "＋"
        if sign == "+"
        else "－"
    )

    return f"""
    <details class="answer-box" hidden>

        <summary>
            答えを確認する
        </summary>

        <div class="answer-title">
            ひっさんで たしかめよう
        </div>

        <div class="answer-problem">

            <div class="answer-top">
                {answer_top_marks(n1, n2, sign)}
            </div>

            <div class="answer-second-row">

                <span class="answer-sign">
                    {display_sign}
                </span>

                <span class="answer-number">
                    {n2}
                </span>

            </div>

            <div class="answer-line"></div>

            <div class="answer-result">
                {answer}
            </div>

        </div>

    </details>
    """


# =========================================================
# メイン画面
# =========================================================


# Dedicated whole-view presentation. Existing sequential implementation is retained verbatim.
WHOLE_VIEW_CSS = '.whole-hint{--cell:44px;font-size:clamp(12px,1.6vw,17px);color:#183b49;max-width:960px;margin:auto;box-sizing:border-box}.whole-hint *{box-sizing:border-box}.whole-hint .wh-top{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center}.whole-hint .wh-steps{list-style:none;padding:0;margin:0;display:grid;gap:3px}.whole-hint .wh-steps li{padding:5px 7px;border-radius:7px;background:#f0f4f6}.whole-hint .wh-steps .active{background:#ffe48c;border:2px solid #b87700;font-weight:bold}.whole-hint .wh-steps .done{background:#e0f3e7;color:#28573a}.whole-hint .wh-written{font-size:30px;background:white;padding:8px;border-radius:12px}.whole-hint .wh-line{display:grid;grid-template-columns:22px repeat(var(--cols),var(--cell));text-align:center;align-items:end;min-height:42px}.whole-hint .wh-line.answer{border-top:2px solid #183b49}.whole-hint .wh-digit{position:relative;min-height:55px;padding-top:22px}.whole-hint .wh-red{position:absolute;top:0;left:0;right:0;color:#c52323;font-size:19px;font-weight:bold}.whole-hint .wh-cross:after{content:\'\';position:absolute;left:8px;right:8px;bottom:15px;border-top:2px solid #c52323;transform:rotate(-40deg)}.whole-hint .wh-work{margin-top:10px;border:2px solid #c7dce3;border-radius:12px;padding:10px;background:#f8fcfd}.whole-hint .wh-rooms{display:grid;grid-template-columns:repeat(var(--cols),minmax(0,1fr));gap:6px}.whole-hint .wh-column{border:1px solid #b6cdd7;border-radius:8px;text-align:center;overflow:hidden;background:white}.whole-hint .wh-head{background:#dbeef3;padding:4px;font-weight:bold}.whole-hint .wh-room{min-height:44px;padding:5px;border-top:1px solid #d6e0e4;display:flex;align-items:center;justify-content:center;flex-direction:column}.whole-hint .wh-special{border:2px solid #cf3939;border-radius:5px;min-height:48px;font-size:.8em;margin:4px}.whole-hint .wh-special b{font-size:22px}.whole-hint .wh-result{font-size:24px;min-height:38px}.whole-hint .wh-action{min-height:100px;text-align:center;padding-top:8px}.whole-hint .wh-prompt{margin:4px 0;font-weight:bold}.whole-hint button{font:inherit;cursor:pointer;border:1px solid #7aadb9;border-radius:8px;background:white;color:#163c4c;padding:7px 12px}.whole-hint input{font:inherit;width:48px;text-align:center;padding:5px;border:2px solid #78a5b7;border-radius:7px;background:white;color:#183b49}.whole-hint .wh-card{display:inline-flex;align-items:center;justify-content:center;font-size:28px;min-width:44px;min-height:44px;margin:4px;touch-action:none;user-select:none;box-shadow:0 3px 0 #9ab0bb;position:relative}.whole-hint .wh-card.lifted{transform:translateY(-7px);box-shadow:0 10px 12px #183b4950}.whole-hint .wh-card.dragging{position:fixed;z-index:9999;margin:0;pointer-events:none;transform:translateY(-7px);box-shadow:0 12px 16px #183b4960}.whole-hint .wh-card.placed{margin:0;box-shadow:none;font-size:24px;min-height:30px;min-width:30px;padding:2px;cursor:default}.whole-hint .wh-dot{font-size:24px;padding:0;width:30px;height:30px;margin:2px;border-radius:50%}.whole-hint .wh-dot.selected{background:#ffcf88;border:2px solid #d94c22}.whole-hint .wh-group{display:inline-grid;grid-template-columns:repeat(5,22px);gap:2px;background:#ffe9d9;border:2px solid #e07a4f;padding:5px;font-size:20px}.whole-hint .wh-feedback{min-height:22px;color:#a33a12;text-align:center;margin:4px 0}.whole-hint .wh-cherry{display:flex;flex-direction:column;align-items:center;gap:4px}.whole-hint .wh-branches{display:flex;justify-content:center;gap:12px}.whole-hint .wh-branch{display:flex;flex-direction:column;align-items:center;font-size:.9em}.whole-hint .wh-hit{background:#fff0b5;outline:2px solid #b87700}.whole-hint .wh-note{text-align:center;color:#385c43;margin:3px 0}.whole-hint .wh-restart{font-size:12px;padding:4px 8px;margin-top:4px}@media(max-width:520px){.whole-hint{--cell:30px;font-size:12px}.whole-hint .wh-top{gap:5px}.whole-hint .wh-written{font-size:25px;padding:3px}.whole-hint .wh-red{font-size:16px}.whole-hint .wh-steps li{padding:3px}.whole-hint .wh-work{padding:5px}.whole-hint .wh-rooms{gap:3px}.whole-hint .wh-special{margin:2px;padding:3px}.whole-hint .wh-branches{gap:5px}.whole-hint .wh-line{min-height:35px}.whole-hint .wh-digit{min-height:49px}.whole-hint .wh-room{min-height:36px}.whole-hint .wh-card{min-width:40px;min-height:40px;font-size:25px}}\n.whole-hint .wh-tokens{flex-direction:row;flex-wrap:wrap;gap:2px}.whole-hint .wh-group span{display:block;font-size:20px;line-height:22px}.whole-hint .wh-steps li{line-height:1.3}.whole-hint button{width:auto}.whole-hint .wh-dot{padding:0;flex:0 0 30px}.whole-hint .wh-card{line-height:1.2}\n.hint-card:has(.whole-hint){width:min(960px,calc(100vw - 28px));position:relative;left:50%;transform:translateX(-50%)}.hint-card:has(.whole-hint)>.answer-box{max-width:484px;margin-left:auto;margin-right:auto}.whole-hint{line-height:1.3}.whole-hint .wh-special{line-height:1.25}.whole-hint .wh-group{grid-template-columns:repeat(5,minmax(0,1fr));max-width:100%;width:122px}.whole-hint .wh-action p{margin:4px 0}@media(max-width:520px){.hint-card:has(.whole-hint){padding:8px}.whole-hint{--cell:27px}.whole-hint .wh-steps{font-size:11px;gap:2px}.whole-hint .wh-special{font-size:10px;min-height:40px}.whole-hint .wh-group{width:90px;padding:3px;gap:0}.whole-hint .wh-group span{font-size:16px;line-height:19px}.whole-hint .wh-card{margin:2px}.whole-hint .wh-room{padding:3px;min-height:33px}.whole-hint .wh-action{min-height:85px}}\n.whole-hint .wh-steps{font-size:14px}.whole-hint .wh-steps li{padding:3px 7px;line-height:1.2}@media(max-width:520px){.whole-hint .wh-steps{font-size:11px}.whole-hint .wh-steps li{padding:3px}}\n.whole-hint .wh-tokens{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));justify-items:center;gap:2px}.whole-hint .wh-dot{margin:0;width:28px;height:28px}@media(max-width:520px){.whole-hint .wh-dot{width:20px;height:20px;font-size:18px}.whole-hint .wh-tokens{padding:3px;gap:2px}}\n.whole-hint .wh-room{min-height:38px}.whole-hint .wh-special{min-height:40px}.whole-hint .wh-steps li{padding:2px 7px}@media(max-width:520px){.whole-hint .wh-room{min-height:30px}.whole-hint .wh-special{min-height:38px}.whole-hint .wh-steps li{padding:2px 3px}}\n\n.whole-hint .wh-card{background:#fff4bf;border:2px solid #937121;border-radius:10px;cursor:grab}.whole-hint .wh-card.placed{box-shadow:0 2px 3px #183b4930;cursor:grab}.whole-hint .wh-error{background:#ffe0e0;border:2px solid #cc3030}.whole-hint .wh-figures{display:flex;flex-wrap:wrap;justify-content:center;gap:3px;font-size:20px;max-width:100%}.whole-hint .wh-hundred{display:inline-flex;align-items:center;justify-content:center;border:2px solid #263238;width:34px;height:28px;font-size:12px;background:white}.whole-hint .red{color:#c52323;border-color:#c52323}.whole-hint .wh-block.red{color:#c52323}.whole-hint .wh-legend{background:white;border:1px solid #b6cdd7;border-radius:8px;padding:8px;margin-bottom:8px}.whole-hint .wh-special{height:82px;min-height:82px}.whole-hint .wh-borrow-stack{display:flex;flex-direction:column;align-items:center;gap:5px}.whole-hint .wh-split{padding:4px;background:#ffe0e0;border:2px solid #c52323}.whole-hint .wh-group{background:#ffe9d9}.whole-hint .wh-room{overflow-wrap:anywhere}\n\n.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{height:170px;min-height:170px;overflow:auto}.whole-hint .wh-card.wh-group{min-width:0;font-size:20px}.whole-hint .wh-special:empty{border-color:transparent}\n\n/* Only the dedicated whole-view hints are affected. */\n.whole-hint .wh-card.wh-order-card{background:#cce7ff;border-color:#3c70a1;color:#173b64}\n.whole-hint .wh-card.dragging{transform:none;cursor:grabbing}\n.whole-hint.wh-drag-portal{position:fixed;inset:0;max-width:none;margin:0;z-index:99999;pointer-events:none}\n.whole-hint.wh-drag-portal *{pointer-events:none}\n.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{height:72px;min-height:72px;overflow:visible}\n.whole-hint .wh-special{height:44px;min-height:44px;border-color:#b6cdd7}\n.whole-hint .wh-special.wh-error{border-color:#cc3030}\n.whole-hint .wh-figures{gap:1px;font-size:16px;line-height:1.1}\n.whole-hint .wh-action{min-height:80px}\n.whole-hint .wh-legend{padding:4px;margin-bottom:5px}\n.whole-hint .wh-work{margin-top:5px;padding:5px}\n@media(max-width:520px){.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{height:64px;min-height:64px}.whole-hint .wh-special{height:34px;min-height:34px}.whole-hint .wh-figures{font-size:14px}.whole-hint .wh-action{min-height:70px}}\n'
WHOLE_VIEW_JS = '(function(){\nconst root=document.querySelector(\'.whole-hint\');if(!root)return;\nconst m=JSON.parse(root.dataset.whole), digit=(n,u)=>Math.floor(n/u)%10;\nconst names={1:\'一のくらい\',10:\'十のくらい\',100:\'百のくらい\',1000:\'千のくらい\'};\nconst circ=n=>String.fromCodePoint(0x2460+n-1);\nconst units=[1,10,...(Math.max(m.n1,m.n2)>=100?[100]:[])];\nconst cols=[...units,...(m.sign===\'+\'&&m.n1+m.n2>=units.at(-1)*10?[units.at(-1)*10]:[])];\nconst place=[\'place\',\'all\'].includes(m.trouble), order=[\'start\',\'all\'].includes(m.trouble), full=[\'carry\',\'borrow\',\'all\'].includes(m.trouble);\nlet actions=[],labels=[];\nfunction label(text){labels.push(text);return labels.length-1;}\nfunction add(kind,step,extra={}){actions.push({kind,step,...extra});}\nlet cherryStep,cardStep,orderStep,calcStep;\nif(place){cherryStep=label(\'さくらんぼを かんせいさせよう\');cardStep=label(\'数字カードを くらいのおへやに いれよう\');\nfor(const row of [\'top\',\'bottom\']){add(\'cherry\',cherryStep,{row});add(\'cards\',cardStep,{row});}}\nif(order){orderStep=label(\'じゅんばんカードを うごかそう\');add(\'order\',orderStep);}\nif(!full)calcStep=label(\'けいさんしよう\');\nlet preview=Object.fromEntries(cols.map(u=>[u,digit(m.n1,u)])),carry=0;\nfor(const u of cols){\n if(m.sign===\'+\'){\n const total=digit(m.n1,u)+digit(m.n2,u)+carry;\n const s=full?label(names[u]+\'の けいさんをしよう\'):calcStep;\n add(\'calc\',s,{u,total,a:digit(m.n1,u),b:digit(m.n2,u),carry});\n if(total>=10&&full){const g=label(\'まとまりを つくって うごかそう\');add(\'group\',g,{u,total});add(\'move\',g,{u,target:u*10});}\n carry=Math.floor(total/10);\n }else{\n const a=preview[u],b=digit(m.n2,u),need=a<b;\n if(full){const s=label(\'けいさんできるかな？\');add(\'check\',s,{u,a,b,need});}\n if(need){let source=u*10;while(preview[source]===0)source*=10;\n const s=full?label(\'まとまりを ばらして うごかそう\'):calcStep;\n while(source>u){add(full?\'break\':\'autoBreak\',s,{source,target:source/10});preview[source]--;preview[source/10]+=10;source/=10;}}\n const s=full?label(names[u]+\'の けいさんをしよう\'):calcStep;\n add(\'calc\',s,{u,total:preview[u]-b,a:preview[u],b,carry:0});\n }}\nlet state,index,selected,split,message;\nfunction reset(){state={placed:{},order:{},locations:{},errors:{},result:{},raw:{},carry:{},changed:{},donated:{},top:Object.fromEntries(cols.map(u=>[u,digit(m.n1,u)])),received:{}};index=0;selected=new Set();split=false;message=\'\';render();}\nconst action=()=>actions[index];\nfunction next(note=\'\'){index++;selected=new Set();split=false;message=note;render();}\nfunction feedback(text){message=text;root.querySelector(\'.wh-feedback\').textContent=text;}\nfunction card(text,key,placed=false,group=false){return `<span class="wh-card${placed?\' placed\':\'\'}${group?\' wh-group\':\'\'}${key.startsWith(\'order-\')?\' wh-order-card\':\'\'}" ${placed&&!key?\'\':`role="button" tabindex="0" aria-label="${group?\'ばらした10こ\':\'カード\'}を うごかす" data-drag="${key}"`}>${text}</span>`;}\nfunction written(){const ordered=[...cols].reverse();let out=\'<div class="wh-written" aria-label="ひっさん">\';\nfor(const row of [\'top\',\'bottom\']){out+=`<div class="wh-line"><span>${row===\'bottom\'?(m.sign===\'+\'?\'＋\':\'−\'):\'\'}</span>`;\nfor(const u of ordered){const n=row===\'top\'?m.n1:m.n2,key=row+\'-\'+u;\nconst value=n<u?\'\':place?(state.placed[key]??\'\'):digit(n,u);\nconst red=row===\'top\'?(state.changed[u]!==undefined?(state.top[u]>=10?\'10\':state.top[u]):(state.carry[u]||\'\')):\'\';\nout+=`<span class="wh-digit${row===\'top\'&&state.donated[u]?\' wh-cross\':\'\'}" data-written="${key}"><small class="wh-red">${red}</small>${value}</span>`;}out+=\'</div>\';}\nconst finalValue=m.sign===\'+\'?m.n1+m.n2:m.n1-m.n2;\nout+=\'<div class="wh-line answer"><span></span>\'+ordered.map(u=>`<span data-answer="${u}">${index===actions.length&&u>Math.max(1,finalValue)?\'\':state.result[u]??\'\'}</span>`).join(\'\')+\'</div></div>\';return out;}\nfunction symbol(u,red=false){return u===1?`<span class="${red?\'red\':\'\'}">○</span>`:u===10?`<span class="wh-block${red?\' red\':\'\'}">${red?\'🟥\':\'■\'}</span>`:`<span class="wh-hundred${red?\' red\':\'\'}">${u}</span>`;}\nfunction figures(n,u,red=false){return `<div class="wh-figures">${Array.from({length:Math.max(0,n)},()=>symbol(u,red)).join(\'\')}</div>`;}\nfunction rooms(){const a=action();let out=\'<div class="wh-rooms">\';\nconst special=[\'carry\',\'borrow\',\'all\'].includes(m.trouble);\nfor(const u of [...cols].reverse()){\nout+=`<div class="wh-column" data-column="${u}"><div class="wh-head">${names[u]}</div>`;\nif(order)out+=`<div class="wh-room wh-special ${state.errors[\'order-\'+u]?\'wh-error\':\'\'}" data-drop="order-${u}">${Object.entries(state.locations).filter(([k,v])=>k.startsWith(\'order-\')&&v===\'order-\'+u).map(([k])=>card(circ(units.indexOf(Number(k.split(\'-\')[1]))+1),k,true)).join(\'\')||(units.includes(u)?\'じゅんばんカードを いれよう\':\'\')}</div>`;\nout+=`<div class="wh-room wh-change">${state.changed[u]&&!(special&&m.sign===\'-\')?\'<b class="red">\'+(state.top[u]>=10?\'10\':state.top[u])+\'</b>\':\'\'}${state.received[u]&&!special?figures(10,u,true):\'\'}</div>`;\nif(special){const carry=m.sign===\'+\'&&u>1, borrow=m.sign===\'-\'&&((a?.kind===\'break\'&&a.target===u)||state.received[u]);out+=`<div class="wh-room wh-special ${state.errors[(carry?\'carry-\':\'break-\')+u]?\'wh-error\':\'\'}" ${carry||borrow?`data-drop="${carry?\'carry-\':\'break-\'}${u}"`:\'\'}>${carry?(state.carry[u]?\'<b class="red">1</b>\'+symbol(u,true):`${names[u/10]}で できた 10のまとまりを いれてね`):borrow?(state.received[u]?\'\':\'まとまりを ばらしたら ここに いれてね\'):\'\'}</div>`;}\nfor(const row of [\'top\',\'bottom\']){const key=row+\'-\'+u,n=row===\'top\'?m.n1:m.n2;\nlet content=\'\';\nif(place){content=Object.entries(state.locations).filter(([k,v])=>(k.startsWith(\'top-\')||k.startsWith(\'bottom-\'))&&v===key).map(([k])=>{const source=Number(k.split(\'-\')[1]),v=digit(m[k.startsWith(\'top-\')?\'n1\':\'n2\'],source);return card(v,k,true)+figures(row===\'top\'&&state.donated[u]&&!state.received[u]?state.top[u]:v,source);}).join(\'\');}\nelse {const v=row===\'top\'?state.top[u]:(n>=u?digit(n,u):\'\');if(v!==\'\')content=card(row===\'top\'?digit(n,u):v,\'\',true)+figures(row===\'top\'&&state.received[u]?digit(n,u):v,u);}\nif(row===\'top\'&&a?.kind===\'break\'&&a.source===u){const count=state.top[u];content=card(count,\'\',true)+\'<div class="wh-figures">\'+Array.from({length:Math.max(0,count-1)},()=>symbol(u)).join(\'\')+(split?card(\'<span>○</span>\'.repeat(10),\'break-\'+a.target,false,true):`<button class="wh-split red" data-split>${symbol(u,true)}</button>` )+\'</div>\';}\nif(row===\'top\'&&state.donated[u]&&full){const original=digit(n,u);content=`<div class="wh-room-number"><span class="wh-original wh-room-cross">${card(original,place?key:\'\',true)}</span><span class="red">${state.top[u]}</span></div>`+figures(state.received[u]?state.top[u]-10:state.top[u],u);}\nif(row===\'top\'&&state.received[u]&&special)content=\'<div class="wh-borrowed"><div class="wh-room-number red">10</div>\'+figures(10,u,true)+\'</div>\'+content;\nout+=`<div class="wh-room ${state.errors[key]?\'wh-error\':\'\'}" data-drop="${key}">${content||(place&&units.includes(u)?\'数字カードを いれよう\':\'\')}</div>`;}\nif(!special)out+=\'<div class="wh-room wh-carry">\'+(state.carry[u]?\'<b class="red">\'+state.carry[u]+\'</b>\'+symbol(u,true):\'\')+\'</div>\';\nconst pending=m.sign===\'+\'&&full&&state.raw[u]>=10&&state.result[u]===undefined;\nconst result=pending?state.raw[u]:state.result[u];let resultFigures=result!==undefined?figures(result,u):\'\';\nif(pending&&a?.u===u&&a.kind===\'group\')resultFigures=\'<div class="wh-figures">\'+Array.from({length:a.total},(_,i)=>`<button class="wh-dot${selected.has(i)?\' selected\':\'\'}" data-dot="${i}">${symbol(u)}</button>`).join(\'\')+\'</div>\';\nif(pending&&a?.u===u&&a.kind===\'move\')resultFigures=\'<div class="wh-figures">\'+card(symbol(a.target,true),\'carry-\'+a.target)+Array.from({length:state.raw[u]%10},()=>symbol(u)).join(\'\')+\'</div>\';\nif(m.sign===\'+\'&&full&&state.raw[u]>=10&&state.result[u]!==undefined)resultFigures=figures(state.raw[u]%10,u);\nconst resultNumber=pending?state.raw[u]:result;\nout+=`<div class="wh-room wh-result" data-room-result="${u}">${resultNumber??\'こたえ\'}${resultFigures}</div>`;\n\nout+=\'</div>\';}\nreturn out+\'</div>\';}\nfunction control(){const a=action();if(!a)return \'<b>できたね！</b>\';\nif(a.kind===\'cherry\'){const n=m[a.row===\'top\'?\'n1\':\'n2\'];return `<div class="wh-cherry"><b style="font-size:26px">${n}</b><span>${units.length===3?\'／\u3000│\u3000＼\':\'／\u3000＼\'}</span><div class="wh-branches">${[...units].reverse().map(u=>`<label class="wh-branch">${u===1?\'1が\':u+\'のまとまり\'}<span><input data-cherry="${u}" inputmode="numeric" aria-label="${n}の${names[u]}の分">こ</span></label>`).join(\'\')}</div><button data-cherry-check>たしかめる</button></div>`;}\nif(a.kind===\'cards\')return \'<p class="wh-prompt">数字カードを くらいのおへやに いれよう</p>\'+[...units].reverse().filter(u=>state.locations[a.row+\'-\'+u]===undefined).map(u=>card(digit(m[a.row===\'top\'?\'n1\':\'n2\'],u),a.row+\'-\'+u)).join(\'\');\nif(a.kind===\'order\')return \'<p class="wh-prompt">じゅんばんカードを 上のおへやに いれよう</p>\'+units.filter(u=>!state.locations[\'order-\'+u]).map((u)=>card(circ(units.indexOf(u)+1),\'order-\'+u)).join(\'\');\nif(a.kind===\'calc\'&&m.sign===\'-\'&&state.received[a.u]&&!full)return `<p class="wh-prompt">${names[a.u]}を けいさんしよう</p><div class="wh-borrow-stack"><div>10${figures(10,a.u)}</div><div>${a.a-10}${figures(a.a-10,a.u)}</div><div>− ${a.b}${figures(a.b,a.u)}</div></div><b>10＋${a.a-10}−${a.b}＝</b><input data-calc inputmode="numeric" aria-label="けいさんのこたえ"><button data-check>たしかめる</button>`;\nif(a.kind===\'calc\'&&m.sign===\'-\'&&state.received[a.u]&&full)return `<p class="wh-prompt">${names[a.u]}を けいさんしよう</p><b>10＋${a.a-10}−${a.b}＝</b><input data-calc inputmode="numeric" aria-label="けいさんのこたえ"><button data-check>たしかめる</button>`;\nif(a.kind===\'calc\')return `<p class="wh-prompt">${names[a.u]}を けいさんしよう</p><span style="font-size:24px">${a.a}${m.sign===\'+\'?\'＋\':\'−\'}${a.b}${a.carry?\'＋\'+a.carry:\'\'}＝</span><input data-calc inputmode="numeric" aria-label="けいさんのこたえ"><button data-check>たしかめる</button>`;\nif(a.kind===\'check\')return `<p class="wh-prompt">${a.a}−${a.b}\u3000このまま けいさんできる？</p><button data-choice="yes">できる</button> <button data-choice="no">けいさんできない</button>`;\nif(a.kind===\'group\')return `<p class="wh-prompt">${a.total}から ${a.u*10}のまとまりを つくって<br>くらいのおへやに いれよう！</p><p>${a.u===1?\'○\':\'■\'}を10こ タップしてみてね</p>`;\nif(a.kind===\'move\')return `<p class="wh-prompt">${a.target}のまとまりが1つできたよ！<br>くり上がりをしよう！</p>`;\nif(a.kind===\'break\'||a.kind===\'autoBreak\')return `<p class="wh-prompt">ひかれる数から${a.source}のまとまりを1つばらしてみよう</p>`+(a.kind===\'autoBreak\'?\'<button data-auto>まとまりを ばらす</button>\':`<p>${split?\'10こを まとめて おへやに うごかそう\':\'■をタップすると ばらばらになるよ\'}</p>`);\nreturn \'\';}\nfunction render(){\nwhile(action()?.kind===\'autoBreak\'){const b=action();applyBreak(b);index++;message=b.target===1?\'10のまとまりを ばらして、一のくらいに うつすよ！\':`${b.source}のまとまりを ばらして、${names[b.target]}に うつすよ！`;}\nroot.dataset.complete=String(index===actions.length&&Object.keys(state.errors).length===0&&Object.keys(state.locations).every(k=>state.locations[k]===k));\nconst box=document.querySelector(\'.answer-box\');if(box){box.hidden=root.dataset.complete!==\'true\';if(box.hidden)box.open=false;}\nconst a=action(),s=a?.step;root.style.setProperty(\'--cols\',cols.length);root.style.setProperty(\'--room-rows\',String(6+(order?1:0)));\nconst past=actions.slice(0,index);\nroot.innerHTML=\'<div class="wh-legend">○＝1\u3000■＝10のまとまり\u3000<span class="wh-hundred">100</span>＝100のまとまり</div><div class="wh-top"><ol class="wh-steps">\'+labels.map((text,i)=>{const done=!actions.slice(index).some(x=>x.step===i);return `<li class="${i===s?\'active\':done?\'done\':\'\'}" ${i===s?\'aria-current="step"\':\'\'}>${done?\'✓\':i===s?\'▶\':\'\'} ${circ(i+1)} ${text}</li>`;}).join(\'\')+\'</ol>\'+written()+\'</div><div class="wh-work">\'+rooms()+\'<div class="wh-action">\'+control()+\'</div></div><p class="wh-feedback" aria-live="polite">\'+message+\'</p><button class="wh-restart" data-reset>さいしょから</button>\';\nroot.querySelector(\'[data-reset]\').onclick=reset;\nroot.querySelectorAll(\'input\').forEach(el=>{el.addEventListener(\'input\',()=>{el.value=el.value.replace(/[^0-9]/g,\'\');});el.addEventListener(\'keydown\',e=>{if(e.key===\'Enter\'){e.preventDefault();root.querySelector(\'[data-cherry-check],[data-check]\')?.click();}});});\nroot.querySelector(\'[data-cherry-check]\')?.addEventListener(\'click\',()=>{const n=m[a.row===\'top\'?\'n1\':\'n2\'];if([...root.querySelectorAll(\'[data-cherry]\')].every(el=>/^(0|[1-9][0-9]*)$/.test(el.value)&&Number(el.value)===digit(n,Number(el.dataset.cherry))))next();else feedback(\'まとまりの数を もういちど たしかめよう。\');});\nroot.querySelector(\'[data-check]\')?.addEventListener(\'click\',()=>{const value=root.querySelector(\'[data-calc]\').value;if(!/^(0|[1-9][0-9]*)$/.test(value)||Number(value)!==a.total){feedback(\'もういちど けいさんしてみよう。\');return;}state.raw[a.u]=a.total;\nif(m.sign===\'+\'&&a.total>=10&&full)delete state.result[a.u];else state.result[a.u]=m.sign===\'+\'?a.total%10:a.total;\nif(m.sign===\'+\'&&a.total>=10&&!full)state.carry[a.u*10]=Math.floor(a.total/10);\nnext(m.sign===\'+\'?(a.total<10?\'くり上がりは ないよ！\':!full?(a.u===1?\'10のまとまりが できたら、十のくらいに うつすよ！\':`10のまとまりが できたら、${names[a.u*10]}に うつすよ！`):\'\'):\'\');});\nroot.querySelectorAll(\'[data-choice]\').forEach(el=>el.onclick=()=>{if((el.dataset.choice===\'no\')!==a.need){feedback(\'数を くらべてみよう。\');return;}next(a.need?\'\':\'くり下がりは ないよ！\');});\nconst splitButton=root.querySelector(\'[data-split]\');if(splitButton){const splitNow=()=>{split=true;render();};splitButton.addEventListener(\'click\',splitNow);splitButton.addEventListener(\'pointerup\',e=>{if(e.pointerType===\'touch\'){e.preventDefault();splitNow();}});}\nroot.querySelector(\'[data-auto]\')?.addEventListener(\'click\',()=>{applyBreak(a);next(`${a.source}のまとまりを 1つ つかったよ。`);});\nroot.querySelectorAll(\'[data-dot]\').forEach(el=>el.onclick=()=>{const i=Number(el.dataset.dot);selected.has(i)?selected.delete(i):selected.add(i);if(selected.size===10)next();else{el.classList.toggle(\'selected\',selected.has(i));}});\nfor(const [key,target] of Object.entries(state.locations)){\n const room=root.querySelector(`[data-drop="${target}"]`);if(!room)continue;\n let el=root.querySelector(`[data-drag="${key}"]`);\n if(!el){const unit=Number(key.split(\'-\')[1]);const value=key.startsWith(\'order-\')?circ(units.indexOf(unit)+1):key.startsWith(\'top-\')||key.startsWith(\'bottom-\')?digit(m[key.startsWith(\'top-\')?\'n1\':\'n2\'],unit):symbol(unit,true);room.insertAdjacentHTML(\'beforeend\',card(value,key,true));el=room.lastElementChild;}\n if(el.parentElement!==room&&!(m.sign===\'-\'&&m.trouble===\'all\'&&key.startsWith(\'top-\')&&state.donated[Number(key.split(\'-\')[1])]&&room.contains(el)))room.appendChild(el);\n}\nroot.querySelectorAll(\'[data-drag]\').forEach(bindDrag);\nrequestAnimationFrame(fitWholeView);\n}\nfunction applyBreak(a){state.donated[a.source]=true;state.top[a.source]--;state.top[a.target]+=10;state.changed[a.source]=true;state.changed[a.target]=true;state.received[a.target]=true;}\nfunction drop(key,target){const a=action();state.locations[key]=target;if(key!==target)delete state.placed[key];\nif((key.startsWith(\'top-\')||key.startsWith(\'bottom-\'))&&key===target)state.placed[key]=digit(m[key.startsWith(\'top-\')?\'n1\':\'n2\'],Number(key.split(\'-\')[1]));\nstate.errors={};for(const [k,v] of Object.entries(state.locations))if(k!==v)state.errors[v]=true;\nif(key!==target){message=key.startsWith(\'order-\')?\'一のくらいからけいさんするよ！ もういちどかんがえなおそう\':key.startsWith(\'top-\')||key.startsWith(\'bottom-\')?`${Number(key.split(\'-\')[1])}が${digit(m[key.startsWith(\'top-\')?\'n1\':\'n2\'],Number(key.split(\'-\')[1]))}こあつまった数だよ！ もういちどかんがえなおそう`:\'まとまりの大きさをかんがえよう！ もういちどかんがえなおそう\';render();return;}\nmessage=\'\';if(a?.kind===\'cards\'&&key.startsWith(a.row+\'-\')){if(units.every(u=>state.locations[a.row+\'-\'+u]===a.row+\'-\'+u))next();else render();}\nelse if(a?.kind===\'order\'&&key.startsWith(\'order-\')){state.order[Number(key.split(\'-\')[1])]=circ(units.indexOf(Number(key.split(\'-\')[1]))+1);if(units.every(u=>state.locations[\'order-\'+u]===\'order-\'+u))next();else render();}\nelse if(a?.kind===\'move\'&&key===\'carry-\'+a.target){state.carry[a.target]=1;state.result[a.u]=state.raw[a.u]%10;delete state.locations[key];next();}\nelse if(a?.kind===\'break\'&&key===\'break-\'+a.target){delete state.locations[key];applyBreak(a);next();}else render();}\nfunction hitRoom(x,y){return [...root.querySelectorAll(\'[data-drop]\')].find(room=>{const r=room.getBoundingClientRect();return x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;});}\nfunction bindDrag(el){let start=null,ghost=null,portal=null,pointer=null;\nel.addEventListener(\'pointerdown\',e=>{\n if(e.button!==0)return;e.preventDefault();const r=el.getBoundingClientRect();\n start={x:e.clientX-r.left,y:e.clientY-r.top};pointer=e.pointerId;\n portal=document.createElement(\'div\');portal.className=\'whole-hint wh-drag-portal\';portal.style.zoom=String(1/(document.body.currentCSSZoom||Number(getComputedStyle(document.body).zoom)||1));\n ghost=el.cloneNode(true);ghost.removeAttribute(\'data-drag\');ghost.classList.add(\'dragging\');\n ghost.style.width=r.width+\'px\';ghost.style.height=r.height+\'px\';ghost.style.left=r.left+\'px\';ghost.style.top=r.top+\'px\';\n portal.appendChild(ghost);document.body.appendChild(portal);el.style.opacity=\'.25\';el.setPointerCapture(pointer);\n});\nel.addEventListener(\'pointermove\',e=>{if(!start||e.pointerId!==pointer)return;\n ghost.style.left=(e.clientX-start.x)+\'px\';ghost.style.top=(e.clientY-start.y)+\'px\';\n const hit=hitRoom(e.clientX,e.clientY);\n root.querySelectorAll(\'[data-drop]\').forEach(room=>room.classList.toggle(\'wh-hit\',room===hit));\n});\nfunction end(e,cancel=false){if(!start||e.pointerId!==pointer)return;\n const hit=cancel?null:hitRoom(e.clientX,e.clientY);\n start=null;portal.remove();el.style.opacity=\'\';if(el.hasPointerCapture(pointer))el.releasePointerCapture(pointer);\n root.querySelectorAll(\'.wh-hit\').forEach(r=>r.classList.remove(\'wh-hit\'));\n if(hit&&root.contains(hit))drop(el.dataset.drag,hit.dataset.drop);\n}\nel.addEventListener(\'pointerup\',e=>end(e));el.addEventListener(\'pointercancel\',e=>end(e,true));\nel.addEventListener(\'keydown\',e=>{if(e.key===\'Enter\'||e.key===\' \'){e.preventDefault();const room=root.querySelector(`[data-drop="${el.dataset.drag}"]`);if(!room)return;room.tabIndex=0;room.focus();room.onkeydown=k=>{if(k.key===\'Enter\'){k.preventDefault();drop(el.dataset.drag,room.dataset.drop);}};}});\n}\nfunction fitWholeView(){const panel=root.closest(\'.hint-card\');if(!panel)return;root.style.zoom=\'1\';root.style.width=\'100%\';const answer=panel.querySelector(\'.answer-box\');const reserved=answer&&!answer.hidden?answer.getBoundingClientRect().height+12:0;const chooser=panel.querySelector(\'[name="choose_hint"]\');const available=panel.clientHeight-reserved-(chooser?chooser.getBoundingClientRect().height+8:0)-20;const scale=Math.min(1,available/root.scrollHeight);root.style.zoom=String(scale);}\nwindow.addEventListener(\'resize\',()=>requestAnimationFrame(fitWholeView));\nreset();\n})();\n'

WHOLE_VIEW_CSS += '\n.whole-hint .wh-column{display:grid;grid-template-rows:28px auto;grid-auto-rows:auto}.whole-hint .wh-change{height:76px;min-height:76px;color:#c52323}.whole-hint .wh-carry{height:54px;min-height:54px}.whole-hint .wh-result{min-height:70px;font-size:20px}.whole-hint .wh-tokens{min-height:115px}.whole-hint .wh-special{height:76px;min-height:76px}.whole-hint .wh-red{font-size:16px}.whole-hint .wh-room[data-drop^="order-"]{font-size:13px}.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{font-size:13px}\n\n.whole-hint .wh-rooms{grid-template-rows:auto}.whole-hint .wh-column{grid-row:span var(--room-rows);grid-template-rows:subgrid}.whole-hint .wh-tokens{height:115px}.whole-hint .wh-change .wh-figures{max-width:130px}\n'

WHOLE_VIEW_CSS += '\n.hint-card:has(.whole-hint){position:fixed;inset:8px;left:8px;transform:none;width:auto;max-width:none;margin:0;padding:10px;z-index:100;overflow:auto;background:#f8fcfd}\n.whole-hint{max-width:none;font-size:14px;width:100%;display:grid;grid-template-columns:minmax(180px,1fr) minmax(0,2fr);gap:6px;align-items:start}\n.whole-hint .wh-legend{grid-column:1/-1;margin:0}\n.whole-hint .wh-top{display:flex;flex-direction:column;gap:6px;align-items:stretch}\n.whole-hint .wh-written{align-self:center}\n.whole-hint .wh-work{margin:0}\n.whole-hint .wh-feedback{grid-column:1/-1;margin:0}\n.whole-hint .wh-restart{justify-self:start;margin:0}\n.whole-hint .wh-change{height:28px;min-height:28px}\n.whole-hint .wh-result{height:auto;min-height:70px}\n.whole-hint .wh-column{grid-template-rows:subgrid}\n.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{height:auto;min-height:74px}\n.whole-hint .wh-room-number{display:flex;justify-content:center;gap:8px;font-size:24px;line-height:1.2}\n.whole-hint .wh-room-number>span{font:inherit;font-weight:inherit}\n.whole-hint .wh-room-number .wh-card{font:inherit;font-weight:inherit;min-width:0;min-height:0;padding:0;margin:0}\n.whole-hint .wh-room-cross{position:relative}\n.whole-hint .wh-room-cross:after{content:\'\';position:absolute;left:-2px;right:-2px;top:50%;border-top:2px solid #c52323;transform:rotate(-40deg)}\n.whole-hint .wh-borrowed{width:100%;margin-bottom:3px}\n.whole-hint .wh-dot{width:24px;height:24px;min-width:24px;min-height:24px;flex:0 0 24px;margin:1px}\n@media(max-width:650px){.whole-hint{grid-template-columns:1fr;font-size:12px}.whole-hint .wh-top{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center}.whole-hint .wh-work{grid-column:1}.whole-hint .wh-steps{font-size:11px}.whole-hint .wh-room[data-drop^="top-"],.whole-hint .wh-room[data-drop^="bottom-"]{min-height:64px}.whole-hint .wh-room-number{font-size:24px}}\n'

# These changes are restricted to the two requested whole-view behaviors.
def _patch_whole_js(original, previous, replacement):
    if previous not in original:
        raise RuntimeError('Required whole-view fix was not applied: ' + previous[:60])
    return original.replace(previous, replacement, 1)

WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    'result:{},raw:{},carry:{},changed:{}',
    'result:{},raw:{},carry:{},carryCompleted:{},changed:{}')
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "const pending=m.sign==='+'&&full&&state.raw[u]>=10&&state.result[u]===undefined;",
    "const pending=m.sign==='+'&&full&&state.raw[u]>=10&&!state.carryCompleted[u];")
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "if(m.sign==='+'&&full&&state.raw[u]>=10&&state.result[u]!==undefined)resultFigures=figures(state.raw[u]%10,u);",
    "if(m.sign==='+'&&full&&state.raw[u]>=10&&state.carryCompleted[u])resultFigures=figures(state.result[u],u);")
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "else if(a?.kind==='move'&&key==='carry-'+a.target){state.carry[a.target]=1;state.result[a.u]=state.raw[a.u]%10;delete state.locations[key];next();}",
    "else if(a?.kind==='move'&&key==='carry-'+a.target&&target==='carry-'+a.target){state.carry[a.target]=1;state.result[a.u]=state.raw[a.u]-10;state.carryCompleted[a.u]=true;delete state.locations[key];next();}")
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    '<span class="wh-original wh-room-cross">${card(original,place?key:\'\',true)}</span><span class="red">${state.top[u]}</span>',
    '<span class="wh-original wh-room-cross" data-borrow-original="${u}">${card(original,place?key:\'\',true)}</span><span class="red" data-borrow-new="${u}">${state.top[u]}</span>')
WHOLE_VIEW_CSS += '\n.whole-hint .wh-room-number [data-borrow-original]{display:inline-flex;position:relative;align-items:center;justify-content:center}.whole-hint .wh-room-number [data-borrow-original]:after{content:"";position:absolute;left:0;right:0;top:50%;border-top:3px solid #c52323;transform:rotate(-40deg);pointer-events:none;z-index:3}.whole-hint .wh-room-number [data-borrow-new]{font:inherit;font-size:inherit;font-weight:inherit;color:#c52323}\n'

# The carry position is the actual completed move state.  Using only the
# separately maintained carryCompleted flag could leave the original 14 on
# screen even after the carried block had appeared in the tens room.
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "const pending=m.sign==='+'&&full&&state.raw[u]>=10&&!state.carryCompleted[u];",
    "const pending=m.sign==='+'&&full&&state.raw[u]>=10&&!state.carry[u*10];")
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "const result=pending?state.raw[u]:state.result[u];let resultFigures=result!==undefined?figures(result,u):'';",
    "const result=pending?state.raw[u]:(m.sign==='+'&&full&&state.raw[u]>=10&&state.carry[u*10]?state.raw[u]%10:state.result[u]);let resultFigures=result!==undefined?figures(result,u):'';")
WHOLE_VIEW_JS = _patch_whole_js(WHOLE_VIEW_JS,
    "if(m.sign==='+'&&full&&state.raw[u]>=10&&state.carryCompleted[u])resultFigures=figures(state.result[u],u);",
    "if(m.sign==='+'&&full&&state.raw[u]>=10&&state.carry[u*10])resultFigures=figures(state.raw[u]%10,u);")

def whole_view_hint(n1, n2, sign, trouble):
    data = html.escape(json.dumps(dict(n1=n1, n2=n2, sign=sign, trouble=trouble), ensure_ascii=False), quote=True)
    return ('<style>' + WHOLE_VIEW_CSS + '</style>'
            + '<div class="whole-hint" data-whole="' + data + '"></div>'
            + '<script>' + WHOLE_VIEW_JS + '</script>')

PAGE = """
<!DOCTYPE html>
<html lang="ja">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
ひっ算 ヒントカード
</title>


<style>

[hidden]{display:none!important}
.hint-written-digit{position:relative;display:inline-block}
.hint-written-red{position:absolute;top:-16px;left:0;right:0;font-size:14px;color:#c52323;line-height:16px}
.hint-written-cross:after{content:'';position:absolute;left:8px;right:8px;top:50%;border-top:2px solid #c52323;transform:rotate(-40deg)}
.answer-top{position:relative}.answer-digit{position:relative;display:inline-block;width:1ch;text-align:center}.answer-red{position:absolute;left:0;right:0;top:-18px;font-size:15px;line-height:18px;color:#c52323}.answer-cross:after{content:'';position:absolute;left:0;right:0;top:50%;border-top:2px solid #c52323;transform:rotate(-40deg)}

* {
    box-sizing: border-box;
}


body {
    margin: 0;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Hiragino Sans",
        "Yu Gothic",
        sans-serif;

    background: #eaf7fa;
    color: #263238;
}


.container {
    max-width: 520px;
    margin: auto;

    padding:
        max(
            18px,
            env(safe-area-inset-top)
        )
        14px
        max(
            40px,
            env(safe-area-inset-bottom)
        );
}


h1 {
    text-align: center;
    font-size: 28px;
    color: #24415a;
    margin: 12px 0 10px;
}


h2 {
    text-align: center;
    font-size: 21px;
    line-height: 1.5;
    color: #24415a;
}


.logout-link {
    display: block;
    text-align: right;
    margin: 0 4px 10px;
    color: #72838c;
    font-size: 12px;
    text-decoration: none;
}


.card,
.hint-card {
    background: white;
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 18px;

    box-shadow:
        0 4px 14px
        rgba(0,0,0,.07);
}


.input-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 13px;
    color: #455a64;
}


.inputs {
    display: grid;

    grid-template-columns:
        1fr
        64px
        1fr;

    gap: 8px;
}


input,
select {
    width: 100%;

    padding:
        13px 7px;

    border:
        2px solid
        #ccd8dd;

    border-radius: 12px;

    text-align: center;
    font-size: 21px;
    background: white;
}


.section-title {
    font-size: 19px;
    font-weight: bold;
    margin: 24px 0 12px;
}


.options {
    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 10px;
}


.choice input {
    display: none;
}


.choice label {
    display: flex;

    flex-direction: column;

    align-items: center;
    justify-content: center;

    min-height: 78px;

    padding:
        10px 6px;

    text-align: center;

    font-size: 15px;
    font-weight: bold;
    line-height: 1.4;

    border:
        3px solid
        transparent;

    border-radius: 15px;

    background: #f0f2f3;
}


.choice input:checked + label {
    background: #fff2a8;
    border-color: #f1c232;
}


.sim-label {
    background:
        #d9f2fb
        !important;
}


.seq-label {
    background:
        #def1df
        !important;
}


.mode-main {
    display: block;
    width: 100%;

    font-size: 20px;
    font-weight: bold;
    line-height: 1.2;

    margin-bottom: 7px;

    white-space: nowrap;
}


.mode-sub {
    display: block;
    width: 100%;

    font-size: 10.5px;
    font-weight: normal;

    white-space: nowrap;
}


.choice input:checked + .sim-label {
    border-color: #49a9d1;
}


.choice input:checked + .seq-label {
    border-color: #62ad68;
}


.submit-button {
    width: 100%;

    margin-top: 20px;

    padding: 17px;

    border: none;

    border-radius: 16px;

    background: #f0a93c;
    color: white;

    font-size: 19px;
    font-weight: bold;
}


/* ======================================================
   問題のひっさん
   ====================================================== */

.problem-card {
    width: 230px;

    margin:
        0 auto 18px;

    padding:
        18px 42px 14px;

    background: white;

    border:
        2px solid
        #455a64;

    border-radius: 12px;

    font-family:
        "Courier New",
        monospace;
}


.problem-number {
    display: block;
    width: 105px;
    margin-left: auto;
    text-align: right;

    font-size: 34px;
    font-weight: bold;
}


.problem-row {
    display: flex;

    align-items: center;
    justify-content: flex-end;

    gap: 14px;
}


.problem-sign {
    font-size: 31px;
    font-weight: bold;
}


.problem-line {
    margin-top: 8px;

    border-bottom:
        3px solid
        #333;
}


/* ======================================================
   凡例・●・■・100
   ====================================================== */

.legend {
    margin-bottom: 18px;
}


.legend-row {
    display: flex;
    align-items: center;
    gap: 10px;

    min-height: 38px;

    font-size: 16px;
}


.circle {
    display: inline-block;

    width: 18px;
    height: 18px;

    margin: 2px;

    vertical-align: middle;

    border-radius: 50%;

    background: #455a64;
}


.square {
    display: inline-block;

    width: 18px;
    height: 18px;

    margin: 2px;

    vertical-align: middle;

    background: #455a64;
}


.big-square {
    width: 32px;
    height: 32px;
}


.hundred-block {
    display: inline-flex;

    align-items: center;
    justify-content: center;

    width: 54px;
    height: 54px;

    margin: 3px;

    border-radius: 8px;

    background: #455a64;

    color: white;

    font-size: 15px;
    font-weight: bold;

    vertical-align: middle;
}


.hundred-block.mini {
    width: 42px;
    height: 36px;

    font-size: 10px;

    border-radius: 7px;
}


.none {
    color: #999;
    font-size: 13px;
}


/* ======================================================
   くらいのおへや
   ====================================================== */

.decomposition {
    margin: 10px 0 18px;

    padding: 13px;

    background: #f2f8fa;

    border-radius: 14px;

    text-align: center;

    font-size: 20px;
    line-height: 1.8;
}


.decomposition b {
    font-size: 23px;
    color: #24415a;
}


.room-table {
    display: grid;

    margin: 10px 0 18px;

    border:
        2px solid
        #555;
}


.room-table.room-2 {
    grid-template-columns:
        repeat(
            2,
            1fr
        );
}


.room-table.room-3 {
    grid-template-columns:
        repeat(
            3,
            1fr
        );
}


.room-head {
    padding: 10px 2px;
    text-align: center;
    font-weight: bold;
    font-size: 15px;

    border-right:
        1px solid
        #555;

    border-bottom:
        2px solid
        #555;
}


.room-cell {
    display: flex;

    align-items: center;
    justify-content: center;

    min-height: 92px;

    padding:
        8px 4px;

    border-right:
        1px solid
        #555;

    border-bottom:
        2px solid
        #555;
}


.room-count {
    padding:
        9px 2px;

    text-align: center;

    line-height: 1.7;
    font-size: 14px;

    border-right:
        1px solid
        #555;
}


.value-row {
    width: 100%;

    display: flex;

    flex-direction: column;

    align-items: center;
    justify-content: center;

    gap: 7px;
}


.value-label {
    font-size: 19px;
    font-weight: bold;

    white-space: nowrap;
}


.symbol-area {
    text-align: center;
    line-height: 1.4;
}


/* ======================================================
   メッセージ
   ====================================================== */

.message {
    margin: 15px 0;

    padding: 14px;

    text-align: center;

    line-height: 1.7;

    font-weight: bold;

    border-radius: 14px;

    background: #fff7ce;
}


.big-message {
    text-align: center;

    font-size: 18px;
    font-weight: bold;
    line-height: 1.7;
}


/* ======================================================
   順番ヒント
   ====================================================== */

.step {
    display: flex;

    align-items: flex-start;

    gap: 14px;

    margin-bottom: 11px;

    padding: 15px;

    background: #f7fafb;

    border-radius: 14px;

    font-size: 17px;
    line-height: 1.7;
}


.step-number {
    display: flex;

    align-items: center;
    justify-content: center;

    min-width: 38px;
    height: 38px;

    border-radius: 50%;

    background: #70b778;

    color: white;

    font-size: 19px;
    font-weight: bold;
}




/* ======================================================
   じゅんばんでみる：1つずつ表示するための「つぎへ」ボタン
   ※ 既存のヒント内容・デザインは変更せず、表示順だけ制御する
   ====================================================== */

.seq-next-button {
    width: 100%;
    margin: 8px 0 14px;
    padding: 15px;
    border: none;
    border-radius: 14px;
    background: #70b778;
    color: white;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}

.seq-next-button:active {
    transform: translateY(1px);
}


/* ======================================================
   どこからヒント
   ====================================================== */

.start-grid {
    display: grid;

    text-align: center;

    border:
        2px solid
        #607d8b;
}


.start-grid.cols-2 {
    grid-template-columns:
        repeat(
            2,
            1fr
        );
}


.start-grid.cols-3 {
    grid-template-columns:
        repeat(
            3,
            1fr
        );
}


.start-title,
.start-number,
.order {
    padding: 10px;

    border-right:
        1px solid
        #607d8b;
}


.start-title {
    font-weight: bold;
}


.start-number {
    font-size: 26px;
    line-height: 1.5;
}


.small-sign {
    font-size: 18px;
    margin-right: 4px;
}


.order span {
    display: inline-flex;

    align-items: center;
    justify-content: center;

    width: 34px;
    height: 34px;

    border-radius: 50%;

    background: #5b9bd5;

    color: white;

    font-size: 18px;
    font-weight: bold;
}


.down-arrow {
    margin: 4px;
    font-size: 22px;
}


.flow {
    margin: 18px auto;

    padding: 12px;

    border-radius: 12px;

    background: #eaf4ff;

    text-align: center;

    font-weight: bold;
    font-size: 18px;
}


/* ======================================================
   全体でみる視覚ヒント
   ====================================================== */

.visual-stage {
    margin: 18px 0;

    padding: 16px;

    border-radius: 18px;

    background: #f7fafb;
}


.stage-title {
    text-align: center;

    margin-bottom: 16px;

    font-size: 18px;
    font-weight: bold;
}


.visual-operation {
    padding:
        16px 10px;

    text-align: center;

    line-height: 2.3;

    border-radius: 16px;

    background: #f1f5f6;
}


.big-operator {
    margin:
        7px 0;

    font-size: 28px;

    text-align: center;
}


.equation {
    margin:
        18px 0;

    text-align: center;

    font-size: 27px;
    font-weight: bold;
}


.group-box {
    margin-top: 16px;

    padding:
        18px 10px;

    text-align: center;

    border-radius: 16px;

    background: #f1f5f6;
}


.remaining-box {
    margin-top: 16px;

    padding:
        16px 10px;

    text-align: center;

    border-radius: 16px;

    background: #ffffff;
}


.symbol-line {
    text-align: center;
    line-height: 1.8;
}


.down-arrow-big {
    margin:
        8px 0;

    text-align: center;

    font-size: 30px;
}


.relation {
    margin-top: 10px;

    text-align: center;

    font-size: 18px;
    font-weight: bold;
}


.move-grid {
    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 10px;

    margin-top: 16px;
}


.move-card {
    padding:
        16px 8px;

    text-align: center;

    border-radius: 16px;

    background: #eef7fa;

    line-height: 1.8;
}


.hundreds-summary {
    text-align: center;
    line-height: 2.2;
}


.carry-card {
    margin: 12px 0;
    padding: 14px;
    border-radius: 14px;
    background: #f5f7f8;
    text-align: center;
    line-height: 1.7;
}


/* ======================================================
   十のくらいのくり上がり：縦にそろえる
   ====================================================== */

.vertical-operation {
    width: 100%;

    max-width: 330px;

    margin:
        0 auto;

    padding:
        18px 10px;

    border-radius: 16px;

    background: #f1f5f6;

    text-align: center;
}


.op-symbol-row {
    min-height: 38px;

    display: flex;

    align-items: center;
    justify-content: center;

    flex-wrap: wrap;
}


.op-plus {
    min-height: 36px;

    display: flex;

    align-items: center;
    justify-content: center;

    font-size: 28px;
    line-height: 1;
}


.op-carry-row {
    min-height: 40px;

    display: flex;

    align-items: center;
    justify-content: center;

    gap: 5px;

    font-size: 15px;
    font-weight: bold;
}


/* ======================================================
   くり下がり・全体
   ====================================================== */

.borrow-notice {
    margin:
        18px 0;

    padding:
        16px;

    border:
        1px solid
        #b9dff1;

    border-radius: 14px;

    background: #edf8fd;

    line-height: 1.8;

    font-weight: bold;

    text-align: left;
}


.borrow-visual-card {
    margin:
        18px 0;

    padding:
        22px 14px;

    border-radius: 18px;

    background: #f7f7f7;

    text-align: center;
}


.borrow-check-wrap {
    margin-top: 18px;

    padding:
        16px 10px;

    border-radius: 18px;

    background: #eef8fc;
}


.borrow-check-title {
    margin-bottom: 12px;

    text-align: center;

    font-size: 18px;
    font-weight: bold;
}


.borrow-check-row {
    display: grid;

    grid-template-columns:
        repeat(
            3,
            minmax(
                0,
                1fr
            )
        );

    gap: 8px;
}


.borrow-check-card {
    min-width: 0;

    padding:
        15px 5px;

    border:
        1px solid
        #b9dff1;

    border-radius: 12px;

    background: white;

    text-align: center;
}


.borrow-place {
    font-size: 17px;
    font-weight: bold;
}


.borrow-calc {
    margin-top: 12px;

    font-size: 18px;

    white-space: nowrap;
}


.borrow-think {
    margin-top: 8px;

    font-size: 15px;
}


/* ======================================================
   答え確認
   ====================================================== */

.answer-box {
    margin:
        22px 0 4px;

    border:
        2px solid
        #f0a93c;

    border-radius: 16px;

    background: #fffaf0;

    overflow: hidden;
}


.answer-box summary {
    cursor: pointer;

    padding: 16px;

    text-align: center;

    font-weight: bold;
    font-size: 18px;

    color: #9a6418;

    list-style: none;
}


.answer-box summary::-webkit-details-marker {
    display: none;
}


.answer-title {
    padding-top: 15px;

    text-align: center;

    font-size: 16px;
    font-weight: bold;

    color: #607d8b;
}


.answer-problem {
    width: 220px;

    margin:
        15px auto 22px;

    padding:
        16px 38px 18px;

    background: white;

    border:
        2px solid
        #607d8b;

    border-radius: 14px;

    font-family:
        "Courier New",
        monospace;
}


.answer-top {
    width: 110px;

    margin-left: auto;

    text-align: right;

    font-size: 34px;
    font-weight: bold;
}


.answer-second-row {
    display: flex;

    align-items: center;
    justify-content: flex-end;

    gap: 14px;
}


.answer-sign {
    font-size: 30px;
    font-weight: bold;
}


.answer-number {
    width: 110px;

    text-align: right;

    font-size: 34px;
    font-weight: bold;
}


.answer-line {
    margin-top: 8px;

    border-bottom:
        3px solid
        #263238;
}


.answer-result {
    width: 110px;

    margin-left: auto;
    margin-top: 8px;

    text-align: right;

    font-size: 34px;
    font-weight: bold;

    color: #24415a;
}


/* ======================================================
   その他
   ====================================================== */

.error {
    margin-bottom: 15px;

    padding: 13px;

    border-radius: 12px;

    background: #ffe2e2;

    color: #a32222;

    font-weight: bold;
}


.subhint h2 {
    margin-top: 24px;
    font-size: 18px;
}


@media(max-width: 390px) {

    .container {
        padding-left: 10px;
        padding-right: 10px;
    }

    h1 {
        font-size: 25px;
    }

    .card,
    .hint-card {
        padding: 14px;
    }

    .mode-main {
        font-size: 18px;
    }

    .mode-sub {
        font-size: 9.5px;
    }

    .room-head {
        font-size: 13px;
    }

    .value-label {
        font-size: 16px;
    }

    .circle,
    .square {
        width: 16px;
        height: 16px;
        margin: 1.5px;
    }

    .big-square {
        width: 30px;
        height: 30px;
    }

    .room-cell {
        min-height: 84px;
    }

    .hundred-block {
        width: 48px;
        height: 48px;
        font-size: 13px;
    }

    .hundred-block.mini {
        width: 40px;
        height: 34px;
        font-size: 9px;
    }

    .move-grid {
        gap: 8px;
    }

    .move-card {
        padding: 13px 5px;
        font-size: 14px;
    }

    .op-carry-row {
        font-size: 13px;
    }

    .borrow-check-wrap {
        padding:
            14px 7px;
    }

    .borrow-check-row {
        gap: 5px;
    }

    .borrow-check-card {
        padding:
            13px 3px;
    }

    .borrow-place {
        font-size: 15px;
    }

    .borrow-calc {
        font-size: 16px;
    }

    .borrow-think {
        font-size: 13px;
    }
}

/* ヒントの操作部分だけ。元の画面とひっさん型のおへやの配色・構造を使用する。 */
.interactive-hint .hint-whole { margin: 12px 0 20px; }
.interactive-hint .room-table.room-4 { grid-template-columns: repeat(4, 1fr); }
.interactive-hint .hint-progress { text-align: right; font-weight: bold; margin-bottom: 8px; }
.interactive-hint .hint-cherries { background: #f8fbfc; border-radius: 12px; padding: 12px; margin-bottom: 14px; }
.interactive-hint .hint-cherry-row { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; margin: 9px 0; }
.interactive-hint .hint-cherry-arrow { color: #456; }
.interactive-hint .hint-decomp-slot { min-width: 48px; min-height: 42px; border: 1px dashed #607d8b; border-radius: 8px; background: white; font-size: 18px; }
.interactive-hint .hint-room-cell { flex-direction: column; text-align: center; cursor: pointer; }
.interactive-hint .hint-room-cell b { font-size: 25px; }
.interactive-hint .hint-order-cell, .interactive-hint .hint-result-cell { text-align: center; cursor: pointer; }
.interactive-hint .hint-symbols { line-height: 1.7; margin-top: 5px; overflow-wrap: anywhere; }
.interactive-hint .hint-unit-token { border: 0; padding: 2px; margin: 1px; background: transparent; font-size: 21px; color: #263238; }
.interactive-hint .hint-unit-token:not(:disabled) { cursor: pointer; }
.interactive-hint .hint-unit-token:disabled { opacity: 1; }
.interactive-hint .hint-unit-token.hint-selected, .interactive-hint .hint-action-card.hint-selected { background: #ffe08a; border-radius: 6px; }
.interactive-hint .hint-carry { font-size: 15px; color: #b44; }
.interactive-hint .hint-one-task { margin-top: 14px; }
.interactive-hint .hint-task-main { width: 100%; }
.interactive-hint .hint-focus { color: #b4232c; font-weight: bold; margin-bottom: 10px; }
.interactive-hint .hint-controls { margin-top: 15px; display: flex; flex-wrap: wrap; align-items: center; gap: 9px; }
.interactive-hint .hint-action-card { min-width: 54px; min-height: 50px; padding: 6px 13px; background: white; border: 2px solid #4b7084; border-radius: 10px; font-size: 23px; cursor: grab; }
.interactive-hint .hint-instruction { font-size: 15px; }
.interactive-hint .hint-input { width: 110px; padding: 9px; border: 1px solid #789; border-radius: 8px; font-size: 21px; }
.interactive-hint .hint-feedback { min-height: 1.8em; margin-top: 12px; font-weight: bold; }
.interactive-hint .hint-navigation { display: flex; justify-content: space-between; gap: 12px; margin-top: 16px; }
.interactive-hint button:disabled { cursor: default; }
.interactive-hint .hint-navigation button:disabled { opacity: .45; }


.interactive-hint .hint-overview-tasks {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:16px;}
.interactive-hint .hint-overview-task {border:1px solid #c5d6df;border-radius:12px;padding:12px;}
.interactive-hint .hint-cherry-input {width:85px;display:block;border-radius:50%;padding:16px;border:2px solid #d99;font-size:20px;}

.interactive-hint .hint-written {position:relative;display:table;margin:0 auto 16px;font-size:30px;}
.interactive-hint .hint-written-row {display:flex;align-items:center;}
.interactive-hint .hint-written-row span {display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;box-sizing:border-box;}
.interactive-hint .hint-red-circle {border:3px solid #d33;border-radius:50%;}
.interactive-hint .hint-written-result {border-top:2px solid #456;font-size:34px;}
.interactive-hint .hint-legend {margin:8px 0;font-size:16px;}

.interactive-hint .hint-hundred {display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:32px;border:2px solid #456;background:white;color:#234;font-size:15px;box-sizing:border-box;}
.interactive-hint .hint-pair-circle {position:absolute;top:0;width:48px;height:96px;border:3px solid #d33;border-radius:50%;box-sizing:border-box;pointer-events:none;}
.interactive-hint .hint-cherry-row {flex-direction:column;align-items:center;gap:2px;}
.interactive-hint .hint-cherry-branches {display:flex;gap:20px;justify-content:center;}
.interactive-hint .hint-decomp-slot {display:flex;align-items:center;gap:4px;flex-wrap:wrap;justify-content:center;max-width:180px;}
</style>
</head>


<body>

<div class="container">


<h1>
    ひっ算 ヒントカード
</h1>


<a
    href="/logout"
    class="logout-link"
>
    ログアウト
</a>


<form method="post" id="hint-selection-form">


<div class="card">


<div class="input-title">
    もんだいを いれてください
</div>


<div class="inputs">


<input
    type="number"
    name="n1"
    min="10"
    max="999"
    value="{{ n1 }}"
    required
>


<select
    name="sign"
    id="sign"
>


<option
    value="+"
    {% if sign == "+" %}
    selected
    {% endif %}
>
    ＋
</option>


<option
    value="-"
    {% if sign == "-" %}
    selected
    {% endif %}
>
    －
</option>


</select>


<input
    type="number"
    name="n2"
    min="10"
    max="999"
    value="{{ n2 }}"
    required
>


</div>


<div class="section-title">
    なにに こまっているかな？
</div>


<div class="options">


<div class="choice">

<input
    type="radio"
    name="trouble"
    value="place"
    id="place"
    {% if trouble == "place" %}
    checked
    {% endif %}
    required
>

<label for="place">
    くらいが
    <br>
    わからない
</label>

</div>


<div class="choice">

<input
    type="radio"
    name="trouble"
    value="start"
    id="start"
    {% if trouble == "start" %}
    checked
    {% endif %}
>

<label for="start">
    どこからやるか
    <br>
    わからない
</label>

</div>


<div class="choice">

<input
    type="radio"
    name="trouble"
    value="carry"
    id="carry"
    {% if trouble == "carry" %}
    checked
    {% endif %}
>

<label
    for="carry"
    id="carry-label"
>

{% if sign == "-" %}

    くり下がりが
    <br>
    むずかしい

{% else %}

    くり上がりが
    <br>
    むずかしい

{% endif %}

</label>

</div>


<div class="choice">

<input
    type="radio"
    name="trouble"
    value="all"
    id="all"
    {% if trouble == "all" %}
    checked
    {% endif %}
>

<label for="all">
    ぜんぶ
    <br>
    むずかしい
</label>

</div>


</div>


<div class="section-title">
    どっちのヒントが
    わかりやすそう？
</div>


<div class="options">


<div class="choice">

<input
    type="radio"
    name="mode"
    value="sim"
    id="sim"
    {% if mode == "sim" %}
    checked
    {% endif %}
    required
>

<label
    for="sim"
    class="sim-label"
>

<span class="mode-main">
    ぜんたいでみる
</span>

<span class="mode-sub">
    ぜんぶを いっしょに見てみよう！
</span>

</label>

</div>


<div class="choice">

<input
    type="radio"
    name="mode"
    value="seq"
    id="seq"
    {% if mode == "seq" %}
    checked
    {% endif %}
>

<label
    for="seq"
    class="seq-label"
>

<span class="mode-main">
    じゅんばんでみる
</span>

<span class="mode-sub">
    1つずつ すすめてみよう！
</span>

</label>

</div>


</div>


<button
    class="submit-button"
    type="submit"
>
    ヒントを見る
</button>


</div>


</form>


{% if error %}

<div class="error">
    {{ error }}
</div>

{% endif %}


{% if hint %}

{{ problem|safe }}

<div class="hint-card">

    <button type="submit" form="hint-selection-form" name="choose_hint" value="1" formnovalidate class="seq-next-button">ヒントをえらぶ</button>

    {{ hint|safe }}

    {{ answer|safe }}

</div>

{% endif %}


</div>


<script>
function calculationMarks(n1,n2,sign,completed){
 const top=Object.fromEntries([1,10,100,1000].map(u=>[u,Math.floor(n1/u)%10]));const red={},cross={};let carry=0;
 for(const u of [1,10,100]){if(!completed.includes(u))break;
 if(sign==='+'){carry=Math.floor((top[u]+Math.floor(n2/u)%10+carry)/10);if(carry)red[u*10]=carry;}
 else if(top[u]<Math.floor(n2/u)%10){let source=u*10;while(top[source]===0)source*=10;while(source>u){top[source]--;cross[source]=true;red[source]=top[source];top[source/10]+=10;red[source/10]=10;source/=10;}}
 }return {red,cross};
}

(function setupInteractiveHint() {
    const root = document.querySelector(".interactive-hint");
    if (!root) return;
    const model = JSON.parse(root.dataset.hint);
    const steps = model.steps;
    const revisedCarry = ["carry","all"].includes(model.trouble);
    const answerCards = model.mode === "sim" && ["place","all"].includes(model.trouble);
    const redCarry = model.mode === "sim" && model.sign === "+" && revisedCarry;
    const body = root.querySelector(".hint-interactive-body");
    const back = root.querySelector(".hint-back");
    const next = root.querySelector(".hint-next");
    const answers = new Map();
    const errors = new Map();
    const units = model.units;
    const displayUnits = model.display_units;
    const names = {1:"一のくらい",10:"十のくらい",100:"百のくらい",1000:"千のくらい"};
    const marks = {1:"⚫",10:"⬛",100:"100",1000:"1000"};
    const hundred = '<span class="hint-hundred">100</span>';
    let current = 0;
    const history = [];
    let chosen = false;
    let selectedDots = new Set();
    let selectedSource = false;

    function escapeText(value) {
        return String(value).replace(/[&<>"']/g, c =>
            ({"&":"&amp;","<":"&lt;",">":"&gt;",[String.fromCharCode(34)]:"&quot;","'":"&#39;"})[c]);
    }
    function digit(number, unit) { return Math.floor(number / unit) % 10; }
    function symbols(unit, count, clickable, kind) {
        let out = "";
        for (let i = 0; i < count; i++) {
            out += `<button type="button" class="hint-unit-token" data-kind="${kind}" data-index="${i}" ${clickable ? "" : "disabled"}>${unit === 100 ? hundred : kind === "borrowed" ? "🔴" : marks[unit] || "■"}</button>`;
        }
        return out;
    }
    function stateThrough(index) {
        const state = {top:{}, bottom:{}, placed:{}, decomp:{}, order:{}, result:{},
                       tokens:{}, pending:{}, carry:{}, borrowed:{}, resultPlaced:{}};
        for (const u of [1,10,100,1000]) {
            state.top[u] = digit(model.n1,u);
            state.bottom[u] = digit(model.n2,u);
        }
        for (let i = 0; i <= index; i++) {
            if (!answers.has(i)) continue;
            const step = steps[i];
            if (["decomp_card","decomp_input"].includes(step.kind)) state.decomp[`${step.row}-${step.unit}`] = step.card;
            if (step.kind === "place_card") state.placed[`${step.row}-${step.unit}`] = step.card;
            if (step.kind === "order_card") state.order[step.unit] = step.card;
            if (step.kind === "result_card") state.resultPlaced[step.unit] = step.card;
            if (step.result) {
                state.result[step.unit] = Number(answers.get(i));
                if (model.sign === "-") state.tokens[step.unit] = Number(answers.get(i));
                if (model.sign === "+") {
                    state.tokens[step.unit] = Number(answers.get(i));
                    if (model.trouble === "start" && Number(answers.get(i)) >= 10)
                        state.carry[step.unit * 10] = 1;
                }
            }
            if (step.kind === "group") {
                state.tokens[step.unit] -= 10;
                state.pending[step.unit * 10] = 1;
            }
            if (step.kind === "move") {
                state.pending[step.target] = 0;
                state.carry[step.target] = 1;
            }
            if (step.kind === "break") {
                state.top[step.source] -= 1;
                state.top[step.target] += 10;
                state.borrowed[step.source] = Math.max(0,(state.borrowed[step.source] || 0)-1);
                state.borrowed[step.target] = (state.borrowed[step.target] || 0)+10;
            }
        }
        return state;
    }
    function writtenCalculation(step) {
        const state = stateThrough(current);
        const ordered = [...displayUnits].reverse();
        const orderQuestion = ["start","all"].includes(model.trouble) && step.kind === "choice" && step.focus && !step.place_pair;
        const pairCircle = !orderQuestion && (revisedCarry || step.place_pair || step.result);
        let out = '<div class="hint-written" aria-label="ひっさん">';
        for (const row of ['top','bottom']) {
            out += `<div class="hint-written-row"><span>${row === 'bottom' ? escapeText(model.sign) : ''}</span>`;
            for (const u of ordered) {
                const number = row === 'top' ? model.n1 : model.n2;
                const value = number < u ? '' : digit(number,u);
                const marks=calculationMarks(model.n1,model.n2,model.sign,steps.slice(0,current+1).filter((s,i)=>answers.has(i)&&s.result).map(s=>s.unit));
                out += `<span data-place="${u}" class="hint-written-digit ${row==='top'&&marks.cross[u]?'hint-written-cross':''}">${row==='top'&&marks.red[u]!==undefined?`<small class="hint-written-red">${marks.red[u]}</small>`:''}${value}</span>`;
            }
            out += '</div>';
        }
        out += '<div class="hint-written-row hint-written-result"><span></span>';
        for (const u of ordered) out += `<span data-result="${u}">${state.result[u] === undefined ? '' : state.result[u] % 10}</span>`;
        out += '</div>';
        if (pairCircle && ordered.includes(step.unit)) out += `<span class="hint-pair-circle" style="left:${48*(ordered.indexOf(step.unit)+1)}px" aria-label="${names[step.unit]}の2つの数字"></span>`;
        return out + '</div>';
    }
    function numericInputs() {
        body.querySelectorAll('.hint-input,.hint-cherry-input').forEach(input => {
            let previous = input.value;
            const valid = value => value === '' || /^(0|[1-9][0-9]*)$/.test(value);
            input.addEventListener('beforeinput', event => {
                if (event.inputType && event.inputType.startsWith('delete')) return;
                if (event.data !== null) {
                    const value = input.value.slice(0,input.selectionStart) + event.data + input.value.slice(input.selectionEnd);
                    if (!valid(value)) event.preventDefault();
                }
            });
            input.addEventListener('input', () => {
                if (valid(input.value)) previous = input.value;
                else input.value = previous;
            });
        });
    }
    function workspace(step) {
        const state = stateThrough(model.mode === "sim" ? steps.length - 1 : current);
        let out = `<div class="hint-whole"><div class="hint-progress">${answers.size} / ${steps.length}</div>`;
        if ((model.trouble === 'place' || model.trouble === 'start' || revisedCarry)) out += `<div class="hint-legend">⚫ ＝ 1　　⬛ ＝ 10のまとまり　　${hundred} ＝ 100のまとまり</div>`;
        if (model.trouble === "place" || model.trouble === "all") {
            out += '<div class="hint-cherries"><b>数を わけてみよう</b>';
            for (const [row,number] of [["top",model.n1],["bottom",model.n2]]) {
                out += `<div class="hint-cherry-row"><b>${number}</b><span class="hint-cherry-arrow">${units.length === 2 ? "↙　↘" : "↙　↓　↘"}</span><div class="hint-cherry-branches">`;
                for (const u of [...units].reverse()) {
                    const key = `${row}-${u}`;
                    out += `<label class="hint-decomp-slot">${u === 1 ? "1が" : u + "のまとまり"}<input class="hint-cherry-input" data-decomp="${key}" type="text" inputmode="numeric" pattern="0|[1-9][0-9]*" aria-label="${number}の${names[u]}の分" value="${escapeText(state.decomp[key] ?? "")}">こ</label>`;
                }
                out += '</div></div>';
            }
            out += '</div>';
        }
        const ordered = [...displayUnits].reverse();
        out += `<div class="room-table room-${displayUnits.length}">`;
        for (const u of ordered) out += `<div class="room-head">${names[u]}のおへや</div>`;
        for (const row of ["top","bottom"]) {
            for (const u of ordered) {
                const key = `${row}-${u}`;
                const show = !units.includes(u) || model.trouble !== "place" && model.trouble !== "all" || state.placed[key];
                const value = !units.includes(u) ? "" : show ? (model.trouble === "place" || model.trouble === "all" ? state.placed[key] : digit(row === "top" ? model.n1 : model.n2,u)) : "□";
                out += `<div class="room-cell hint-room-cell" data-row="${row}" data-target="${key}"><div><b>${escapeText(value)}</b>`;
                if (show && (row === "top" || (model.trouble === "start" || revisedCarry) || answerCards)) {
                    const count = row === "top" ? state.top[u] : state.bottom[u];
                    out += `<div class="hint-symbols">${symbols(u,count-(row === "top" ? state.borrowed[u] || 0 : 0),row === "top" && step.kind === "break" && step.source === u,"source") + (row === "top" ? symbols(u,state.borrowed[u] || 0,u !== 1 && step.kind === "break" && step.source === u,u === 1 ? "borrowed" : "source") : "")}</div>`;
                    if (row === "top" && state.carry[u]) out += `<div class="hint-carry">＋${redCarry && u === 10 ? "🟥" : u === 100 ? hundred : marks[u] || "■"}</div>`;
                }
                out += '</div></div>';
            }
        }
        if (["start","all"].includes(model.trouble)) for (const u of ordered) out += `<div class="room-cell hint-order-cell" data-target="${u}">じゅんばん<br><b>${escapeText(state.order[u] || "□")}</b></div>`;
        const digitResult = model.mode === "sim" && ["place","start","all"].includes(model.trouble);
        if (model.trouble !== "place" || answerCards) for (const u of ordered) {
            const total = answerCards ? state.resultPlaced[u] : state.result[u];
            out += `<div class="room-cell hint-result-cell" data-target="result-${u}" style="${revisedCarry || digitResult ? "flex-direction:column" : ""}">${(model.trouble === "start" || revisedCarry || digitResult) ? "" : "答え<br>"}<b style="${(model.trouble === "start" || revisedCarry || digitResult) ? "font-size:30px" : ""}">${total === undefined ? "□" : !digitResult && revisedCarry && model.sign === "+" && state.tokens[u] >= 10 ? total : total % 10}</b>`;
            if (digitResult && total !== undefined)
                out += `<div class="hint-symbols">${symbols(u,Number(total) % 10,false,"result")}</div>`;
            // Keep grouping tokens available until the all-hint answer card is placed.
            if (state.tokens[u] !== undefined && (model.trouble === "carry" || model.trouble === "all" && total === undefined))
                out += `<div class="hint-symbols">${symbols(u,state.tokens[u],step.kind === "group" && step.unit === u,"group")}</div>`;
            out += '</div>';
        }
        out += '</div></div>';
        return out;
    }
    function smallHint(step, attempts) {
        if (attempts === 1) {
            if (step.kind === "decomp_card" || step.kind === "place_card" || step.kind === "order_card") return "いちばん右から くらいを 見てみよう。";
            if (step.kind === "group" || step.kind === "move" || step.kind === "break") return "10こで ひとつの まとまりを 作ってみよう。";
            return "数字と くらいを もういちど 見てみよう。";
        }
        if (step.kind === "move") return "10のまとまりは、一のくらいの ひとつ左へ うつすよ。";
        if (step.kind === "break") return "ひとつ左のくらいの まとまりを ばらそう。";
        if (step.kind === "order_card") return "一のくらいから 右→左の じゅんばんだよ。";
        if (step.kind === "group") return "●を 10こ えらんでみよう。";
        return "10ずつの まとまりを かぞえてみよう。";
    }
    function submit(value) {
        const step = steps[current];
        const normalized = String(value).trim();
        if (['number','decomp_input'].includes(step.kind) && !/^(0|[1-9][0-9]*)$/.test(String(value))) {
            body.querySelector('.hint-feedback').textContent = '0か、それより大きい数を 入れよう。さいしょに0をつけないでね。';
            return;
        }
        if (normalized === String(step.answer)) {
            if (!answers.has(current)) history.push(current);
            answers.set(current, normalized);
            errors.delete(current);
            chosen = false;
            selectedSource = false;
            selectedDots = new Set();
            show("そうだね！ " + (step.kind === "break" ? "まとまりが 10こに かわったね。" :
                step.kind === "group" ? "10こが ひとつの まとまりに なったね。" : "できたよ。"));
        } else {
            const attempts = (errors.get(current) || 0) + 1;
            errors.set(current, attempts);
            if(model.mode === "seq") {const box=document.querySelector(".answer-box");if(box){box.hidden=true;box.open=false;}for(const j of [...answers.keys()]) if(j >= current) answers.delete(j);next.disabled=true;}
            body.querySelector(".hint-feedback").textContent = smallHint(step,attempts);
        }
    }
    function bindWorkspace(step) {
        if (step.kind === "group") {
            body.querySelectorAll('[data-kind="group"]').forEach(button => {
                button.addEventListener("click", () => {
                    const index = Number(button.dataset.index);
                    if (selectedDots.has(index)) selectedDots.delete(index); else selectedDots.add(index);
                    button.classList.toggle("hint-selected",selectedDots.has(index));
                    if (selectedDots.size === 10) submit(10);
                });
            });
        }
        if (step.kind === "break") {
            body.querySelectorAll('[data-kind="source"]').forEach(button => {
                button.addEventListener("click", event => {
                    event.stopPropagation();
                    selectedSource = true;
                    button.classList.add("hint-selected");
                });
                button.draggable = true;
                button.addEventListener("dragstart", () => { selectedSource = true; });
            });
        }
        // The complete destination column, including headings, gaps and result area.
        if (revisedCarry && step.kind === 'move') {
            const table = body.querySelector('.room-table');
            const moveToColumn = event => {
                if (!chosen) return;
                const rect = table.getBoundingClientRect();
                const column = Math.floor((event.clientX - rect.left) / (rect.width / displayUnits.length));
                const unit = [...displayUnits].reverse()[column];
                if (unit !== undefined) {event.preventDefault();event.stopPropagation();submit(String(unit));}
            };
            table.addEventListener('click',moveToColumn,true);
            table.addEventListener('drop',moveToColumn,true);
            table.addEventListener('dragover',event => event.preventDefault());
        }
        body.querySelectorAll("[data-target]").forEach(target => {
            target.addEventListener("click", () => {
                if (["place","all"].includes(model.trouble)) step = steps[current];
                if (step.kind === "break") {
                    if (!target.classList.contains("hint-room-cell") || target.dataset.row !== "top") return;
                    if (!selectedSource) { body.querySelector(".hint-feedback").textContent = "先に まとまりを ひとつ えらぼう。"; return; }
                    submit(`${step.source}-${target.dataset.target.split("-").pop()}`);
                } else if (chosen) {
                    if (step.kind === "move") {
                        if (!target.classList.contains("hint-room-cell") || target.dataset.row !== "top") return;
                        submit(target.dataset.target.split("-").pop());
                    } else if (step.kind === "decomp_card" && target.classList.contains("hint-decomp-slot") ||
                               step.kind === "place_card" && target.classList.contains("hint-room-cell") ||
                               step.kind === "order_card" && target.classList.contains("hint-order-cell") ||
                               step.kind === "result_card" && target.classList.contains("hint-result-cell")) {
                        submit(target.dataset.target);
                    }
                }
            });
            target.addEventListener("dragover", event => event.preventDefault());
            target.addEventListener("drop", event => {
                if (["place","all"].includes(model.trouble)) step = steps[current];
                event.preventDefault();
                if (!chosen && !selectedSource) return;
                if (step.kind === "break" && target.classList.contains("hint-room-cell") && target.dataset.row === "top")
                    submit(`${step.source}-${target.dataset.target.split("-").pop()}`);
                else if (step.kind === "move" && target.classList.contains("hint-room-cell") && target.dataset.row === "top")
                    submit(target.dataset.target.split("-").pop());
                else if (step.kind === "decomp_card" && target.classList.contains("hint-decomp-slot") ||
                         step.kind === "place_card" && target.classList.contains("hint-room-cell") ||
                         step.kind === "order_card" && target.classList.contains("hint-order-cell") ||
                         step.kind === "result_card" && target.classList.contains("hint-result-cell"))
                    submit(target.dataset.target);
            });
        });
    }
    function control(step) {
        let out = "";
        if (["decomp_card","place_card","order_card","result_card","move"].includes(step.kind)) {
            const card = step.kind === "move" ? (redCarry && step.target === 10 ? "🟥" : marks[step.target] || "■") : step.card;
            out = `<button type="button" draggable="true" class="hint-action-card">${step.kind === "move" && step.target === 100 ? hundred : escapeText(card)}</button><span class="hint-instruction">カードを えらんで おへやに おこう</span>`;
        } else if (step.kind === "break") {
            out = '<span class="hint-instruction">上の おへやの まとまりを 1こ えらび、うつす先を えらぼう</span>';
        } else if (step.kind === "group") {
            out = revisedCarry ? `<span class="hint-instruction">${marks[step.unit]}を10こ えらぼう</span>` : '<span class="hint-instruction">答えの まとまりを 10こ えらぼう</span>';
        } else if (step.options) {
            out = step.options.map(option => `<button type="button" class="seq-next-button hint-choice" data-choice="${escapeText(option)}">${escapeText(option)}</button>`).join("");
        } else {
            out = '<input class="hint-input" type="text" inputmode="numeric" pattern="0|[1-9][0-9]*" aria-label="こたえ">'
                + '<button type="button" class="seq-next-button hint-check">たしかめる</button>';
        }
        return out;
    }

    function ready(i) {
        const step = steps[i];
        if (["decomp_input", "place_card", "order_card"].includes(step.kind)) {
            if (step.kind === "place_card") return steps.every((s,j) => s.kind !== "decomp_input" || answers.has(j));
            if (step.kind === "order_card") return steps.every((s,j) => !["decomp_input","place_card"].includes(s.kind) || answers.has(j));
            return true;
        }
        return steps.slice(0,i).every((s,j) => answers.has(j));
    }
    function showWhole(message) {
        if (answers.has(current) || !ready(current)) current = steps.findIndex((s,i) => !answers.has(i) && ready(i));
        if (current < 0) current = steps.length - 1;
        const step = steps[current];
        chosen = false; selectedSource = false; selectedDots = new Set();
        body.innerHTML = workspace(step) + '<div class="hint-overview-tasks">' + steps.map((s,i) => {
            if (s.kind === "decomp_input") return '';
            const enabled = ready(i), done = answers.has(i);
            const question = enabled || done ? s.question.replace('{entered}',answers.get(s.reflect) || '□') :
                (s.result ? names[s.unit] + 'の けいさん（前の さぎょうのあとでけいさんがかわるよ）' : 'まとまりの さぎょう');
            return `<div class="hint-overview-task" data-task="${i}"><b>${escapeText(question)}</b>`
                + (done ? `<div>✓ ${escapeText(s.result ? answers.get(i) : ["place_card","order_card","result_card"].includes(s.kind) ? s.card : 'できたよ')}</div>` : enabled ? `<div class="hint-controls">${control(s)}</div>` : '<div>前の さぎょうを たしかめよう</div>')
                + (enabled && s.notice ? `<p>${escapeText(s.notice)}</p>` : '') + '</div>';
        }).join('') + '</div><div class="hint-feedback" aria-live="polite">' + escapeText(message || '') + '</div>';
        body.querySelectorAll('[data-decomp]').forEach(input => {
            const i = steps.findIndex(s => s.kind === 'decomp_input' && `${s.row}-${s.unit}` === input.dataset.decomp);
            input.disabled = answers.has(i);
            const check = () => {current = i;submit(input.value);};
            input.addEventListener('change',check);
            input.addEventListener('keydown',e => {if(e.key === 'Enter'){e.preventDefault();check();}});
        });
        body.querySelectorAll('[data-task]').forEach(panel => {
            const i = Number(panel.dataset.task);
            const card = panel.querySelector('.hint-action-card');
            if(card) {
                const pick = () => {current=i;chosen=true;card.classList.add('hint-selected');};
                card.addEventListener('click',pick);card.addEventListener('dragstart',pick);
            }
            panel.querySelectorAll('[data-choice]').forEach(button => button.addEventListener('click',()=>{current=i;submit(button.dataset.choice);}));
            const input=panel.querySelector('.hint-input');
            if(input){const check=()=>{current=i;submit(input.value);};panel.querySelector('.hint-check').addEventListener('click',check);input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();check();}});}
        });
        // Token operations have one dependency-ready action, while all earlier results stay visible.
        bindWorkspace(step);
        numericInputs();
        back.disabled = !history.length;
        next.hidden = true;
        if(answers.size === steps.length) body.querySelector('.hint-feedback').textContent += ' できた！';
    }

    function show(message) {
        const box=document.querySelector(".answer-box");
        if(box){box.hidden=!(current===steps.length-1&&steps.every((s,i)=>answers.has(i)));if(box.hidden)box.open=false;}
        if(model.mode === "sim") {showWhole(message);return;}
        const step = steps[current];
        const question = step.reflect === undefined ? step.question :
            step.question.replace("{entered}",answers.get(step.reflect) || "□");
        chosen = false;
        selectedSource = false;
        selectedDots = new Set();
        const focus = model.mode === "seq" && step.focus ? `<div class="hint-focus">${step.row ? [...String(model[step.row === 'top' ? 'n1' : 'n2'])].map((d,i,a) => (10 ** (a.length-i-1) === step.unit ? `<span class="hint-selected" style="border:3px solid #d33;border-radius:50%;padding:4px">${d}</span>` : d)).join('') : escapeText(step.focus)}</div>` : "";
        body.innerHTML = ((model.trouble === "start" || revisedCarry) || model.trouble === "place" && (step.place_pair || step.result || answers.has(current) && steps[current + 1]?.place_pair) ? writtenCalculation(step) : "")
            + `<div class="step hint-one-task"><span class="step-number">${current + 1}</span><div class="hint-task-main">`
            + focus + (step.notice ? `<p>${escapeText(step.notice)}</p>` : "") + `<b>${escapeText(question)}</b><div class="hint-controls">${control(step)}</div>`
            + `<div class="hint-feedback" aria-live="polite">${escapeText(message || "")}</div></div></div>`;
        const actionCard = body.querySelector(".hint-action-card");
        if (actionCard) {
            actionCard.addEventListener("click", () => { chosen = true; actionCard.classList.add("hint-selected"); });
            actionCard.addEventListener("dragstart", () => { chosen = true; });
        }
        body.querySelectorAll("[data-choice]").forEach(button => button.addEventListener("click", () => submit(button.dataset.choice)));
        const input = body.querySelector(".hint-input");
        if (input) {
            if (answers.has(current)) input.value = answers.get(current);
            const check = () => submit(input.value);
            body.querySelector(".hint-check").addEventListener("click",check);
            input.addEventListener("keydown",event => { if (event.key === "Enter") {event.preventDefault();check();} });
        }
        if (model.mode === "sim") bindWorkspace(step);
        numericInputs();
        back.disabled = current === 0;
        next.disabled = !answers.has(current) || current === steps.length - 1;
        if (current === steps.length - 1 && answers.has(current))
            body.querySelector(".hint-feedback").textContent += " できた！";
    }
    back.addEventListener("click", () => {
        if(model.mode === "sim") {if(history.length){const i=history.pop();for(const j of [...answers.keys()]) if(j>=i) answers.delete(j);while(history.length && history[history.length-1]>=i)history.pop();current=i;show();}}
        else if (current > 0) {current--;show();}
    });
    next.addEventListener("click", () => { if (answers.has(current) && current < steps.length - 1) {current++;show();} });
    if (steps.length) show();
})();



const sign =
    document.getElementById(
        "sign"
    );


const carryLabel =
    document.getElementById(
        "carry-label"
    );


function updateCarryLabel() {

    if (sign.value === "-") {

        carryLabel.innerHTML =
            "くり下がりが<br>むずかしい";

    }

    else {

        carryLabel.innerHTML =
            "くり上がりが<br>むずかしい";

    }

}


sign.addEventListener(
    "change",
    updateCarryLabel
);

// =========================================================
// 「じゅんばんでみる」を1手順ずつ表示
// =========================================================

(function setupSequentialHint() {

    const selectedMode = "{{ mode }}";

    if (selectedMode !== "seq") {
        return;
    }

    const hintCard = document.querySelector(".hint-card");

    if (!hintCard) {
        return;
    }

    if (hintCard.querySelector(".interactive-hint")) {
        return;
    }

    const steps = Array.from(
        hintCard.querySelectorAll(".step")
    );

    if (steps.length <= 1) {
        return;
    }

    // 最初は①だけを表示する。
    steps.forEach((step, index) => {
        step.style.display = index === 0 ? "flex" : "none";
    });

    // くらいのヒントの最後にあるまとめメッセージは、
    // 最終手順まで進んだあとに表示する。
    const lastStep = steps[steps.length - 1];
    const finalMessages = [];
    let nextElement = lastStep.nextElementSibling;

    while (nextElement) {
        if (nextElement.classList.contains("answer-box")) {
            break;
        }

        finalMessages.push(nextElement);
        nextElement = nextElement.nextElementSibling;
    }

    finalMessages.forEach((element) => {
        element.style.display = "none";
    });

    let currentIndex = 0;

    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.className = "seq-next-button";
    nextButton.textContent = "つぎへ";

    function placeNextButton() {
        if (currentIndex >= steps.length - 1) {
            nextButton.remove();

            finalMessages.forEach((element) => {
                element.style.display = "";
            });

            return;
        }

        steps[currentIndex].insertAdjacentElement(
            "afterend",
            nextButton
        );
    }

    nextButton.addEventListener("click", function() {

        steps[currentIndex].style.display = "none";
        currentIndex += 1;
        steps[currentIndex].style.display = "flex";

        placeNextButton();

        steps[currentIndex].scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
    });

    placeNextButton();

})();


</script>

</body>
</html>
"""


# =========================================================
# メイン
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    if not session.get("logged_in"):
        return redirect(
            url_for("login")
        )

    n1 = 35
    n2 = 29
    sign = "+"

    trouble = ""
    mode = ""

    hint = ""
    problem = ""
    answer = ""
    error = ""

    if request.method == "POST":

        try:

            n1 = int(
                request.form.get(
                    "n1",
                    35
                )
            )

            n2 = int(
                request.form.get(
                    "n2",
                    29
                )
            )

            sign = request.form.get(
                "sign",
                "+"
            )

            trouble = request.form.get(
                "trouble",
                ""
            )

            mode = request.form.get(
                "mode",
                ""
            )

            if request.form.get("choose_hint") == "1":
                trouble = ""
                mode = ""

            elif not (
                10 <= n1 <= 999
                and
                10 <= n2 <= 999
            ):

                error = (
                    "10〜999までの数を "
                    "いれてください。"
                )

            elif (
                sign == "-"
                and
                n1 < n2
            ):

                error = (
                    "ひき算では、"
                    "上の数を下の数より "
                    "大きくしてください。"
                )

            elif not trouble:

                error = (
                    "こまっていることを "
                    "えらんでください。"
                )

            elif not mode:

                error = (
                    "ヒントの見かたを "
                    "えらんでください。"
                )

            else:

                problem = problem_html(
                    n1,
                    n2,
                    sign
                )

                if trouble in ("place", "start", "carry", "all") and mode in ("sim", "seq"):
                    hint = whole_view_hint(n1, n2, sign, trouble) if mode == "sim" else interactive_hint(n1, n2, sign, trouble, mode)

                answer = answer_html(
                    n1,
                    n2,
                    sign
                )

        except ValueError:

            error = (
                "すうじを "
                "正しく 入れてください。"
            )

    return render_template_string(
        PAGE,

        n1=n1,
        n2=n2,
        sign=sign,

        trouble=trouble,
        mode=mode,

        hint=hint,
        problem=problem,
        answer=answer,
        error=error
    )


# =========================================================
# 起動
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

