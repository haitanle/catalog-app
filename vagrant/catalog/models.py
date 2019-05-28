from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	username = Column(String, nullable=False)
	password = Column(String, nullable=True) #password not needed - log in with only OAuth
	email = Column(String)

	teams = relationship("Team")
	players = relationship("Player")


class Team(Base):
	__tablename__ = 'team'

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'))
	players = relationship("Player")

	@property
	def serialize(self):
		return {
			'teamName': self.name
		}
	

class Player(Base):
	__tablename__ = 'player'

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	user_id = Column(Integer, ForeignKey('user.id'))
	bio = Column(String, nullable= True)
	position = Column(String)
	team_id = Column(Integer, ForeignKey('team.id'))

	@property
	def serialize(self):
		return {
			'playerName': self.name,
			'position': self.position,
			'bio': self.bio
		}


engine = create_engine('sqlite:///soccerCatalog.db')
Base.metadata.create_all(engine)

