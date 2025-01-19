from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

app = Flask(__name__)

# Cấu hình kết nối cơ sở dữ liệu SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Thư mục lưu file tải lên
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# Tạo bảng Questions trong cơ sở dữ liệu
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(200), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    answer = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Question {self.question_text}>"

# Khởi tạo cơ sở dữ liệu nếu chưa có
with app.app_context():
    db.create_all()

# Trang chủ
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/delete_question/<int:id>', methods=['GET'])
def delete_question(id):
    question_to_delete = Question.query.get(id)
    if question_to_delete:
        db.session.delete(question_to_delete)
        db.session.commit()
    return redirect(url_for('index'))

# Trang để tải lên file Excel
@app.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel():
    file_name = None  # Variable to hold the file name
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        if file and file.filename.endswith('.xlsx'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Set the file name to display in the template
            file_name = file.filename

            # Đọc file Excel và lưu vào cơ sở dữ liệu
            try:
                df = pd.read_excel(filepath)
                for _, row in df.iterrows():
                    question = Question(
                        question_text=row['Question'],
                        option1=row['Option1'],
                        option2=row['Option2'],
                        option3=row['Option3'],
                        option4=row['Option4'],
                        answer=row['Answer']
                    )
                    db.session.add(question)
                db.session.commit()
            except Exception as e:
                return f"Error processing file: {e}", 500

            return render_template('upload_excel.html', file_name=file_name)

    return render_template('upload_excel.html', file_name=file_name)

# Trang quiz để người dùng làm bài
@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    # Lấy thời gian giới hạn từ query string
    time_limit = request.args.get('time_limit', type=int, default=0)
    questions = Question.query.all()

    if request.method == 'POST':
        score = 0
        for idx, question in enumerate(questions):
            user_answer = request.form.get(f'question-{idx}')
            if user_answer == question.answer:
                score += 1
        return render_template('result.html', score=score, total=len(questions))

    return render_template('quiz.html', questions=questions, time_limit=time_limit)
@app.route('/result', methods=['POST'])
def result():
    score = 0
    total = len(questions)
    incorrect_questions = []
# Duyệt qua từng câu hỏi để kiểm tra câu trả lời
    for i, question in enumerate(questions):
        user_answer = request.form.get(f"question-{i}")
        correct_answer = question['correct_answer']
        if user_answer == correct_answer:
            score += 1
        else:
            incorrect_questions.append({
                'index': i,
                'question_text': question['question_text']
            })

    return render_template('result.html', score=score, total=total, incorrect_questions=incorrect_questions)

# Route để xóa tất cả câu hỏi
@app.route('/delete_all_questions', methods=['GET'])
def delete_all_questions():
    # Xóa tất cả câu hỏi trong bảng Question
    Question.query.delete()
    db.session.commit()
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
