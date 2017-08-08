from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catagory, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Bob Marley", email="bobmarley@gmail.com",
             picture='https://pbs.twimg.com/profile_images/503662325614665728/rAlA-uhV_400x400.jpeg')
session.add(User1)
session.commit()

# Catagory for "My Little Ponies"
catagory1 = Catagory(user_id=1, name="My Little Pony")

session.add(catagory1)
session.commit()

catagoryItem = Item(user_id=1, name="Pinkie Pie", description="I'm not giving him cake, I'm ASSAULTING him with cake!!",
                     image="images/Pinkie_Pie.svg", catagory=catagory1)

session.add(catagoryItem)
session.commit()


catagoryItem2 = Item(user_id=1, name="Apple Jack", description="Tutu based off of Apple Jack from My Little Ponies.",
                     image="images/applejack.svg", catagory=catagory1)

session.add(catagoryItem2)
session.commit()

catagoryItem3 = Item(user_id=1, name="Rainbow Dash", description="Tutu based off of Rainbow Dash from My Little Pony.",
                     image="images/RainbowDash.svg", catagory=catagory1)

session.add(catagoryItem3)
session.commit()

catagoryItem4 = Item(user_id=1, name="Twilight Sparkle", description="Tutu based off of Twilight from My Little Pony.",
                     image="images/twilight.svg", catagory=catagory1)

session.add(catagoryItem4)
session.commit()

catagoryItem5 = Item(user_id=1, name="Fluttershy", description="Tutu based off of Fluttershy from My Little Pony.",
                     image="images/fluttershy.svg", catagory=catagory1)

session.add(catagoryItem5)
session.commit()

catagoryItem6 = Item(user_id=1, name="Rarity", description="Tutu based off of Rarity from My Little Pony.",
                     image="images/rarity.svg", catagory=catagory1)

session.add(catagoryItem6)
session.commit()



print "added menu items!"
