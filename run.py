import sys
import math  # For calculations
import tweepy  # Python library for accessing twitter API
import time  # For delay effect
import warnings  # Remove warnings
import matplotlib.pyplot as mpl  # For graph
import networkx as nx  # For graph and metrics


# The function takes the username as an input which is basically the 'startingPoint' given in the main function.
# The username is converted into processable form of an id and I displayed it twice to confirm the screen name matched
# with username that was provided. For the basis of graph this will be considered as generator of initial node.
def fetchMyAccount(username):
    print('Username : ', username)
    init_id = api.get_user(username)
    init_id = init_id.id
    user = api.get_user(init_id)
    screen_name = user.screen_name
    print('Screen Name : ', screen_name)
    unique_nodes.add(init_id)
    init_node = (init_id, init_id)
    return init_node


# The function getFriends() return a list of ids of users that are being followed by the specified user.
def getFriends(uid):
    ids = []
    # A cursor from tweepy is used so as to take care of the paging issue and keep the number of users to 5000
    cur = tweepy.Cursor(api.friends_ids, id=uid).items(5000)
    # Try and except statement allows the program to handle the scenarios when a private account is encountered or when
    # the Twitter API reaches it limits.
    # Please wait when the limit is reached the program will start where it left from.
    while True:
        try:
            friendId = cur.next()
            ids.append(friendId)
        except tweepy.TweepError as error:
            if error.reason == "Not authorized.":
                print('A possible private account encountered!')
                break
            else:
                print(error)
                print('Limit Reached, Please Wait!')
                time.sleep(60)  # Purposely used to delay frequent printing wait message
                continue
        except StopIteration:
            break
    return ids


# The function getFollowers() return a list of ids of users that follow the specified user.
def getFollowers(uid):
    ids = []
    cur = tweepy.Cursor(api.followers_ids, id=uid).items(5000)
    while True:
        try:
            followerId = cur.next()
            ids.append(followerId)
        except tweepy.TweepError as error:
            if error.reason == "Not authorized.":
                print('Ignoring Private user')
                break
            else:
                print('Limit Reached, Please Wait!')
                time.sleep(60)
                continue
        except StopIteration:
            break
    return ids


# The function commonAccounts() helps the program in finding the intersections between the friends and followers list
def commonAccounts(friendIds, followerIds):
    friendSet = set(friendIds)
    followerSet = set(followerIds)
    common_list = list(friendSet.intersection(followerSet))
    return common_list


# The function mostPopularAccount() is used to fetch the 5 most followed account from the common list.
# Here I have used api.lookup_user which has a constraint of only processing 100 user or nodes in a go. Therefore,
# there is a need to divide the data into parts of 100 if it is greater than 100.
def mostPopularAccounts(commons):
    popularAccounts = []
    users = []
    result = []
    length = len(commons)
    parts = math.ceil(length / 100)  # Identifying the number of partitions that would be required
    if length <= 0:  # In case there are no accounts found
        return []
    if length > 100:
        for part in range(parts):
            start = part * 100
            end = start + 100
            temp = api.lookup_users(commons[start:end])
            users = users + temp
    else:
        users = api.lookup_users(commons)
    for user in users:
        record = (user.id, user.followers_count)
        popularAccounts.append(record)
    popularAccounts.sort(key=lambda x: x[1], reverse=True)  # Sorting(Desc Order) by followers count of each record
    fivePopularAccounts = popularAccounts[:5]  # First five account with highest followers
    for popUser in fivePopularAccounts:
        result.append(popUser[0])
    return result


# The crawler() function the main crawler that processes every node of the program.
def crawler(newStartPoint):
    followers = getFollowers(newStartPoint)
    friends = getFriends(newStartPoint)
    commons = commonAccounts(friends, followers)
    popularFriends = mostPopularAccounts(commons)
    unique_nodes.update(popularFriends)
    records = []
    for friend in popularFriends:
        record = (newStartPoint, friend)
        records.append(record)
    return records


# The getGraph() function is used to gain the metrics as well as the graph on the basis of data received.
def getGraph(edges):
    graph = nx.Graph()
    graph.add_edges_from(edges)
    nodes, edges = len(graph.nodes), len(graph.edges)
    diameter = nx.diameter(graph)
    averageDistance = nx.average_shortest_path_length(graph)
    metricFile = open(startingPoint + '.txt', 'w')
    metricFile.write('Total Nodes = ' + str(nodes))
    metricFile.write('\nTotal Edges = ' + str(edges))
    metricFile.write('\nAverage Distance = ' + str(averageDistance))
    metricFile.write('\nDiameter = ' + str(diameter))
    metricFile.close()
    nx.draw(graph, with_labels=True)
    mpl.savefig(startingPoint + '.png', dpi=420)
    mpl.show()


# The driver function
if __name__ == '__main__':
    # Keys and Tokens obtained from developers account
    OAUTH_TOKEN = ""
    OAUTH_TOKEN_SECRET = ""
    CONSUMER_KEY = ""
    CONSUMER_SECRET = ""

    # Specifying the username of the account to be used as starting point
    startingPoint = 'POTUS'

    # Authentication into the account via Tweepy
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    api = tweepy.API(auth)

    warnings.filterwarnings("ignore", category=UserWarning)  # Ignore unnecessary warnings
    unprocessedEdges, processedEdges = [], []
    unique_nodes = set()  # Used to keep distinct accounts/nodes/users
    node = fetchMyAccount(startingPoint)
    unprocessedEdges.append(node)
    unprocessedCount = len(unprocessedEdges)
    totalNodes = 0

    # The conditional looping allows the program to run till the maximum of 100 nodes and till each are processed
    while unprocessedCount > 0 and totalNodes < 100:
        pEdge = unprocessedEdges[0]
        unprocessedEdges = unprocessedEdges[1:]
        new_edges = crawler(pEdge[1])
        unprocessedEdges = unprocessedEdges + new_edges
        processedEdges.append(pEdge)
        unprocessedCount = len(unprocessedEdges)
        totalNodes = len(unique_nodes)
        print(totalNodes, 'nodes have been processed')

    processedEdges = processedEdges + unprocessedEdges
    getGraph(processedEdges)
