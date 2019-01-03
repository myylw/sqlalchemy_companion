# 创建父类
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

####################################   定义表   ################################################################
# 各种关系配置详见:https://docs.sqlalchemy.org/en/latest/orm/relationships.html

# 导入字段类型
from sqlalchemy import Column
from sqlalchemy import String, Integer, Text, DateTime, Boolean


# 普通定义
class Test(Base):  # 必须继承于declarative_base的实例
    # 注:有的数据库有自己特殊的字段类型,在sqlclchemy中被称为方言,这些方言字段都在sqlalchemy.dialects中

    # 定义表名(必须定义)
    __tablename__ = 'test'

    # 定义字段
    # id字段,int型,主键,自增,主键是必须的
    id = Column(Integer, primary_key=True, autoincrement=True)

    # name字段,varchar型,48位,不许为空,唯一约束
    name = Column(String(64), nullable=False, unique=True)

    # nick_name字段,varchar型,48位,索引
    nick_name = Column(String(64), index=True)

    # date字段,datetime型,根据生成行的时间自动添加时间,在更新时会自动更新时间
    from datetime import datetime
    date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # 还可以自定义字段名,这个字段的默认值是创建这个表的时间(所有的行都是这个时间)
    date2 = Column(DateTime, name='new_date', default=datetime.now())

    # content字段,Text型,默认值1234,server_default是设置在表上的默认值
    from sqlalchemy import text
    content = Column(Text, server_default=text('1234'))

    # deleted字段,布尔型,默认为0(布尔字段设置默认值方法比较特殊)
    deleted = Column(Boolean, default=False, server_default=text('0'))

    # 复合约束和索引
    from sqlalchemy import UniqueConstraint, Index
    __table_args__ = (
        UniqueConstraint('id', 'name', name='id_name'),  # 联合唯一键约束
        Index('name', 'nick_name', 'date')  # 联合索引,符合最左原则
    )

    # 其他的方言字段
    from sqlalchemy.dialects.mysql import LONGTEXT, TINYINT, INTEGER  # mysql的方言(还有好多)
    integer = Column(INTEGER(unsigned=True))  # 无符号整数
    from sqlalchemy.dialects.oracle import DATE  # oracle的方言(还有别的数据库的方言都在dialects中)

    # 如果表中的字段名和python的名词空间有冲突, 则可以改字段名
    _import = Column(String(64), name='import')


#####################################################   一对多关系   ###################################################
# https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html#one-to-many
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


class OneToMany(Base):
    # 注:大多数关系型数据库的FK只能连接到主键或者具有unique约束的键上
    # 注2:FK也可以引用自己,为自关联(自引用)

    __tablename__ = 'one_to_many'
    __table_args__ = {'mysql_engine': 'InnoDB'}  # 可以自选引擎
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 写法1,定义外键,外键为表名.字段名(光写表名不行,必须详细到字段),级联更新
    test_id = Column(Integer, ForeignKey('test.id', onupdate='CASCADE'))
    # 写法2,这种需注意类定义的顺序,还可以给外键改名字
    test_id = Column(Integer, ForeignKey(Test.id, name='fk_onetomany_test'))

    # 关系定义(还有好多属性详见sqlalchemy.schema.RelationshipProperty)
    test = relationship('Test', order_by="Test.name")  # 必须写类名
    # relationship API详见:https://docs.sqlalchemy.org/en/latest/orm/relationship_api.html?highlight=relationship#sqlalchemy.orm.relationship

    # 级联删除设置
    # 级联删除详见: https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#tutorial-delete-cascade
    # one删除,many不受影响
    test_id = Column(Integer, ForeignKey('test.id', ondelete='CASCADE'))
    test = relationship('Test', backref=backref('one_to_many', passive_deletes=True))
    # backref详见:https://docs.sqlalchemy.org/en/latest/orm/backref.html

    # one删除,many也删除
    test = relationship('Test', backref=backref('one_to_many', cascade="all,delete"))

    # one删除,many不删除,但是FK改为null
    test = relationship('Test', backref=backref('one_to_many'))  # 使用了反向引用就可以不再主表里写relationship也直接能用了,但是.运算符不提示
    test = relationship('Test', back_populates="one_to_many")  # 新写法,和上面的等价

    # 只在一个表中添加relationship字段是可以的,为单向反射(无法反查)
    # backref是反向引用,一个表中的relationship中定义了backref,那么在另一个关系表中就直接找到对应的行
    # 不用backref也是可以的,详见sqlalchemy.schema.RelationshipProperty的属性
    # relationship 不在那边那边就是多的一方


# 使用外键操作有利于保证数据的完整性和一致性,但效率会低一些相比手工控制


#######################################################  多对多关系  #############################################
# https://docs.sqlalchemy.org/en/latest/orm/tutorial.html#orm-tutorial-many-to-many
# 多对多关系是用两个一对多关系来表示的,也就是说需要一张中间表
from sqlalchemy import Table

# 中间表
a_b = Table('a_b',
            Base.metadata,
            Column('a_id', Integer, ForeignKey('a.id'), primary_key=True),
            Column('b_id', Integer, ForeignKey('b.id'), primary_key=True)
            )


class A(Base):
    __tablename__ = 'a'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    b = relationship('B',  # 必须写类名
                     secondary=a_b,  # 中间表
                     cascade="delete, delete-orphan",  # 级联删除
                     single_parent=True,  # 多对多级联删除
                     passive_deletes=True  # 关联删除
                     )
    # b = relationship('b', secondary=a_b,backref=backref('a')) 也可以写反向引用,这样就不用再b中写relationship了,但是这样用.的时候就不提示了


class B(Base):
    __tablename__ = 'b'
    id = Column(Integer, primary_key=True)
    content = Column(String(32), nullable=False)
    a = relationship('A', secondary=a_b)  # 必须写类名


###################################################   配置连接   ###########################################

DIALECT = 'mysql'  # 要用的什么数据库
DRIVER = 'pymysql'  # 连接数据库驱动
USERNAME = 'root'  # 用户名
PASSWORD = '123456'  # 密码
HOST = 'localhost'  # 服务器
PORT = '3306'  # 端口
DATABASE = 'test2'  # 数据库名

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,
                                                                       DATABASE)

##################################################   创建engine   ##########################################
from sqlalchemy import create_engine

# 填入配置字符串就可以创建引擎了.echo=True是控制台显示日志开关
engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)

##################################################   创建session  ##########################################
from sqlalchemy.orm import sessionmaker

# 线程不安全session
Session = sessionmaker(bind=engine)  # sessionmaker要绑定engine
session = Session()  # 多线程的情况下使用同一个session是不安全的,某个线程进行了session.commit()操作,其他线程的数据也会被提交

# 配置流程:配置字符串-->创建engine-->创建session
# session.add() 添加要提交的对象
# session.commit() 提交到数据库


##### 对于web请求用于多线程的session套路
from sqlalchemy.orm import scoped_session

Session = scoped_session(sessionmaker())  # 线程公用的
# 线程中
session = Session()  # 每个线程都用自己的session
# do someting
# session.add(XXXX)
# session.commit()
Session.remove()  # 用完了就remove

# session的设置
sessionmaker(autocommit=False, autoflush=False)


# 注:mysql默认的隔离级别是可重复读


##################################################  创建和删除表   ##############################################

# 创建一个表
def create_tables(tables=None):
    Base.metadata.create_all(engine, tables)


# 全部创建
def create_all_tables():
    Base.metadata.create_all(bind=engine)


# 全部删除
def drop_all():
    Base.metadata.drop_all(bind=engine)


# 建议还是用Navicat或者Workbench之类的工具操作模型来生成表
# 或者使用sqlalchemy创建表,然后再用Navicat或Workbench逆向到模型来验证

#################################################   增删改查   ###############################################

# 示例表
teacher_student = Table('teacher_student',
                        Base.metadata,
                        Column('teacher_id', Integer, ForeignKey('teacher.id'), primary_key=True),  # 别忘了外键
                        Column('student_id', Integer, ForeignKey('student.id'), primary_key=True)
                        )


class Teacher(Base):
    __tablename__ = 'teacher'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    student = relationship('Student', secondary=teacher_student, backref=backref('teacher'))  # 一个是类名一个是表名


class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)


# 有反向引用无须relationsh

#################################################  增  #######################################################
# 增方法1
t1 = Teacher(name='teacher1')
s1 = Student(name='student1')
s2 = Student(name='student2')
t1.student = [s1, s2]  # 添加关系(必须用列表)
session.add(t1)  # 每个都要添加到session
session.add(s1)
session.add(s2)
session.commit()  # 提交

# 使用add_all
s3 = Student(name='student1')
s4 = Student(name='student1')
s5 = Student(name='student1')
session.add_all((s3, s4, s5))  # 批量add
session.commit()

# 大批量增,此方法速度极快,相比普通orm快几个数量级
session.execute(Student.__table__.insert(), [{'name': 'haha'} for _ in range(10)])
session.commit()

###################################################   查  ################################################
# 全查回来
students = session.query(Student).all()
[print(student.name) for student in students]

# 限制数量
students = session.query(Student).limit(5).all()  # 就查5行回来

# 查一个
students = session.query(Student).one()  # 没查到抛出sqlalchemy.orm.exc.NoResultFound,MultipleResultsFound
students = session.query(Student).one_or_none()  # 如果没查到就返回一个none,如果有多行就抛MultipleResultsFound异常
students = session.query(Student).first()  # 如果没查到就返回一个none,如果有多个就返回第一个,并不会抛异常
students = session.query(Student).filter(Student.id == '3').scalar()  # 如果没查到就返回一个none,如果有多行就抛MultipleResultsFound异常
# 注:所有异常都在sqlalchemy.orm.exc中

# 偏移行
students = session.query(Student).offset(5).all()

# 添加查询条件
students = session.query(Student).filter(Student.name == 'student1').all()
students = session.query(Student).filter(Student.name != 'student1').all()  # 不等
students = session.query(Student).filter(Student.id >= '2').all()  # ><也成
students = session.query(Student).filter(Student.id >= '2', Student.name != 'student1').all()  # 多条件,每个条件都要满足(and关系)
[print(student.name) for student in students]

# 添加查询条件方法2
students = session.query(Student).filter_by(id=10).first()
# 这种方法效果和filter一样,但是filter_by使用了关键字传参的方式,filter是表达式

# 查并且排序
students = session.query(Student).filter(Student.name != 'student1').order_by(Student.id).all()
students = session.query(Student).filter(Student.name != 'student1').order_by(Student.id.desc()).all()
students = session.query(Student).filter(Student.name != 'student1').order_by('id desc').all()  # 和上面功能相同,只是写法不同
[print(student.name, student.id) for student in students]

# 多查询条件or,not关系
from sqlalchemy import or_, not_

students = session.query(Student).filter(or_(Student.id == '5', Student.name == 'student1')).all()
students = session.query(Student).filter(not_(Student.id == '5', Student.name == 'student1')).all()

# in成员运算
students = session.query(Student).filter(Student.id.in_(5, 6)).all()
# 注:in运算出的结果不支持删除

# 聚合函数
from sqlalchemy import func
#func.count：统计行的数量
# func.avg：求平均值
# func.max：求最大值
# func.min：求最小值
# func.sum：求和
print(session.query(func.count('*')).select_from(Student).scalar())
print(session.query(func.count('*')).filter(Student.id > 6).scalar())  # 带条件

# 求和
print('!', session.query(func.sum(Student.id)).scalar())

# 多对一,多对多查
# 例一
student = session.query(Student).filter(Student.id == 18).first()  # 多对多查返回一个列表
[print(teacher.name) for teacher in student.teacher]
# 例二
teachers = session.query(Teacher).filter(Teacher.id > 6).all()
[[print(s.name) for s in teacher.student] for teacher in teachers]

#######################################################  改  #######################################

# 改可以查回来,改好了提交回去,但是速度会低一点
student = session.query(Student).filter(Student.id == 16).first()
student.name = 'zzzz'
session.commit()

# 快一点的方法,不生成映射对象
session.query(Student).filter_by(id=15).update({'name': '12345'})
session.commit()

# 配合scoped_session和行级锁可解决线程安全

#####################################################   行级锁   ####################################
# 读锁(共享锁)
# 查询的时候如果用了读锁,那么其他线程想修改该行就得等锁被释放
# 因为读锁假设情况是查回来的数据不修改,所以其他的线程也可以读,但是要修改的话就得用写锁比较安全
session1 = Session()
session2 = Session()
s1 = session1.query(Student).with_lockmode('read').filter(Student.name == 'bingfa').first()
s2 = session2.query(Student).with_lockmode('read').filter(Student.name == 'bingfa').first()  # 因为是共享锁,其他session也可以查
s1.name = '1234'
session1.add(s1)
session1.commit()  # 被阻塞,因为session2给这行加了读锁
print(s1.name, s2.name)  # 被阻塞

# 写锁(互斥锁)
# 写锁假设的是你要修改这个数据,所以你不改完了提交谁也读写不了这行
session1 = Session()
session2 = Session()
s1 = session1.query(Student).with_lockmode('update').filter(Student.name == 'bingfa').first()
s2 = session2.query(Student).with_lockmode('read').filter(Student.name == 'bingfa').first()  # 被阻塞,因为该行被加了写锁
s1.name = 'hah'  # 被阻塞
session1.add(s1)  # 被阻塞
session1.commit()  # 被阻塞
print(s1.name, s2.name)  # 被阻塞

# 读写锁形式2
student = session.Query(Student).with_for_update(read=True).filter(Student.name == 'bingfa').first()  # 读锁,共享锁
student = session.Query(Student).with_for_update(read=False).filter(Student.name == 'bingfa').first()  # 写锁,互斥锁
# 该函数完整形式:with_for_update（nowait = False，read = False，of = None，skip_locked = False，key_share = False ）
# nowait: 其他事务碰到锁是等待还是抛异常,默认等待
# read: 表示锁模式,默认是读锁
# of: 表示哪个表上锁,默认为和此次查询有关的所有表

#######################################################  删  ################################################
s = session.query(Student).filter(Student.id == 11).delete()  # 在示例表中无法运行,因为示例表是多对多关系,只能删除关联表记录,不能删除子表记录
session.commit()  # 别忘了提交
# 在query上操作是绕过orm的效率很高

# 多对多删除需要关注级联设置,级联设置关系到能否删除

# 多对多可以这样删除关系
s = session.query(Student).filter(Student.id == 19).first()
s.teacher = []
session.commit()
