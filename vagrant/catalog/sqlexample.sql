PRAGMA foreign_keys = ON;

insert into user(username,password) values('Tan','123');

# good 
insert into team(name,user_id) values('Barcelona',1);

# bad 
insert into team(name,user_id) values('Juventus',1);

insert into team(name,user_id) values('Chelsea',1);


#good 
insert into player(name,user_id,team_id,bio) values('Ronaldo',1,1,"Cristiano Ronaldo dos Santos Aveiro GOIH ComM is a Portuguese professional footballer who plays as a forward for Italian club Juventus and captains the Portugal national team.");
insert into player(name,user_id,team_id,bio) values('mandzukic',1,1,"Mario Mandžukić is a Croatian professional footballer who plays as a forward for Italian club Juventus. Besides being a prolific goalscorer, he is known for his defensive contribution and aerial power.");
insert into player(name,user_id,team_id) values('Dybala',1,1);

insert into player(name,user_id,team_id,bio) values('Kevin De Buyne',1,2,"Kevin De Bruyne is a Belgian professional footballer who plays as a midfielder for English club Manchester City and the Belgian national team");
insert into player(name,user_id,team_id,bio) values('Gabriel Jesus',1,2,"Gabriel Fernando de Jesus, commonly known as Gabriel Jesus, is a Brazilian professional footballer who plays as a forward for Premier League club Manchester City and the Brazil national team. Jesus began his career at Palmeiras.");

insert into player(name,user_id,team_id,bio) values('Ngolo Konte',1,3,"N'Golo Kanté is a French professional footballer who plays as a defensive midfielder for Premier League club Chelsea and the France national team. He made his senior debut at Boulogne and then spent two seasons at Caen, the latter in Ligue 1.");
insert into player(name,user_id,team_id,bio) values('Eden Hazard',1,3,"Eden Michael Hazard is a Belgian professional footballer who plays for Premier League club Chelsea and captains the Belgium national team. Primarily playing as an attacking midfielder and as a wide midfielder, Hazard is known for his creativity, speed, dribbling and excellent passing");


insert into player(name,user_id,team_id) values('Ronaldo',5,1);

#good 
insert into player(name,)



alter table player add column position String;